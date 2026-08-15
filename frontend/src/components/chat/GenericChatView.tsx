// F:\Kernschmied\frontend\src\components\chat\GenericChatView.tsx

import { useEffect, useRef, useState } from 'react';
import { useAppStoreState, selectSelectedNode } from '../../store';
import { CornerUpLeft, MessageCircle, Send, Square, X } from 'lucide-react';
import IconBadge from '../common/IconBadge';
import WorkspaceLayout from '../layout/WorkspaceLayout';
import useEffectiveWidgets from '../../hooks/useEffectiveWidgets';
import { getWidgetRenderer } from '../../registry/widgetRegistry';
import { DynamicIcon } from '../../registry/iconRegistry';
import { getNodeTypeConfig } from '../../config/nodeTypeConfig';

import type { FormEvent, KeyboardEvent } from 'react';

import { ApiError, apiPostStream } from '../../api/client';
import { apiGet } from '../../api/client';
import { useChatHistory } from '../../hooks/useChatHistory';
import { loadUserPreferences } from '../../auth/auth-api';
import { loadMentionCandidates } from '../../api/mentions';
import type { MentionCandidate } from '../../api/mentions';

import type { ApiStreamHandle } from '../../api/client';

const SOURCE_FILE = 'frontend/src/components/chat/GenericChatView.tsx';
const CHAT_STREAM_PATH = '/chat/stream';
const CHAT_STREAM_SCHEMA_VERSION = '1.0' as const;
const MAX_MESSAGE_LENGTH = 50_000;
const MAX_INPUT_HEIGHT = 192;

/* ============================================================
 * TYPEN
 * ============================================================ */

type GenericChatViewProps = {
  title: string;
  hierarchyNodeId: string;
  hierarchyNodeType: string;
};

type ChatRole = 'user' | 'assistant' | 'system';

type ChatRequestStatus = 'idle' | 'connecting' | 'streaming' | 'completed' | 'failed' | 'cancelled';

type ChatMessageStatus = 'pending' | 'streaming' | 'completed' | 'failed' | 'cancelled';

type ChatMessage = {
  id: string;
  role: ChatRole;
  content: string;
  timestamp: number;
  status: ChatMessageStatus;
  requestId?: string;
  conversationId?: string;
  serverMessageId?: string;
  authorName?: string;
  parentMessageId?: string;
  directedToUser?: boolean;
};

type ChatRequestPayload = {
  message: string;
  conversation_id: string | null;
  parent_message_id: string | null;
  hierarchy_node_id: string;
  model_id: string | null;
  tool_ids: string[];
  mentions: Array<{ user_id: string }>;
  ai_response: boolean | null;
  metadata: Record<string, unknown>;
};

/* ============================================================
 * HILFSFUNKTIONEN (unverändert, aber gekürzt)
 * ============================================================ */

function createMessageId(): string {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID();
  }
  return ['message', Date.now().toString(36), Math.random().toString(36).slice(2)].join('-');
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function asOptionalString(value: unknown): string | null {
  if (typeof value !== 'string') return null;
  const normalized = value.trim();
  return normalized || null;
}

function asOptionalSequence(value: unknown): number | null {
  let candidate: number;
  if (typeof value === 'number') candidate = value;
  else if (typeof value === 'string' && value.trim() !== '') candidate = Number(value);
  else return null;
  if (!Number.isSafeInteger(candidate) || candidate < 0) return null;
  return candidate;
}

function normalizeSseBuffer(value: string): string {
  return value.replace(/\r\n/g, '\n').replace(/\r/g, '\n');
}

function isAbortError(error: unknown): boolean {
  return error instanceof DOMException && error.name === 'AbortError';
}

function validatePrompt(value: string): string {
  const normalized = value.trim();
  if (!normalized) throw new Error('Die Nachricht darf nicht leer sein.');
  if (normalized.length > MAX_MESSAGE_LENGTH) {
    throw new Error(
      `Die Nachricht darf höchstens ${MAX_MESSAGE_LENGTH.toLocaleString('de-DE')} Zeichen enthalten.`
    );
  }
  return normalized;
}

function validateChatRequest(request: ChatRequestPayload): void {
  if (!request.hierarchy_node_id.trim()) {
    throw new Error('Für die Chat-Anfrage wurde kein gültiger Hierarchieknoten angegeben.');
  }
  if (
    !Array.isArray(request.tool_ids) ||
    !request.tool_ids.every((toolId) => typeof toolId === 'string' && toolId.trim().length > 0)
  ) {
    throw new Error('Die Tool-IDs der Chat-Anfrage sind ungültig.');
  }
  if (!isRecord(request.metadata)) {
    throw new Error('Die Metadaten der Chat-Anfrage sind ungültig.');
  }
}

function formatTime(timestamp: number): string {
  return new Date(timestamp).toLocaleTimeString('de-DE', {
    hour: '2-digit',
    minute: '2-digit',
  });
}

function getInitials(role: ChatRole): string {
  switch (role) {
    case 'user':
      return 'DU';
    case 'assistant':
      return 'KI';
    default:
      return 'SY';
  }
}

function getDeliveryStatus(message: ChatMessage): string {
  if (message.status === 'pending') return message.role === 'assistant' ? 'KI wird vorbereitet' : 'Wird gesendet';
  if (message.status === 'streaming') return 'KI verarbeitet die Anfrage';
  if (message.status === 'failed') return 'Übertragung fehlgeschlagen';
  if (message.status === 'cancelled') return 'Abgebrochen';
  if (message.role === 'assistant') return 'KI-Antwort abgeschlossen';
  return message.directedToUser ? 'An Benutzer zugestellt' : 'Vom Chatserver verarbeitet';
}

function getAccessibleRequestStatus(status: ChatRequestStatus): string {
  switch (status) {
    case 'connecting':
      return 'Die Verbindung zum Chatserver wird aufgebaut.';
    case 'streaming':
      return 'Die Antwort wird erstellt.';
    case 'completed':
      return 'Die Antwort wurde vollständig empfangen.';
    case 'failed':
      return 'Die Chat-Anfrage ist fehlgeschlagen.';
    case 'cancelled':
      return 'Die Chat-Anfrage wurde abgebrochen.';
    default:
      return 'Der Chat ist bereit.';
  }
}

function formatRequestError(error: unknown): string {
  if (error instanceof ApiError) {
    const reference = error.requestId ? ` Request-ID: ${error.requestId}.` : '';
    return `${error.message}${reference}`;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return 'Die Nachricht konnte nicht gesendet werden.';
}

function extractContentFromPayload(payload: unknown): string {
  if (typeof payload === 'string') return payload;
  if (!isRecord(payload)) return '';
  if (typeof payload.content === 'string') return payload.content;
  if (typeof payload.text === 'string') return payload.text;
  if (typeof payload.token === 'string') return payload.token;
  if (isRecord(payload.token)) {
    if (typeof payload.token.content === 'string') return payload.token.content;
    if (typeof payload.token.text === 'string') return payload.token.text;
  }
  if (typeof payload.delta === 'string') return payload.delta;
  if (isRecord(payload.delta) && typeof payload.delta.content === 'string') return payload.delta.content;
  if (typeof payload.message === 'string') return payload.message;
  if (isRecord(payload.message) && typeof payload.message.content === 'string') return payload.message.content;
  return '';
}

function extractErrorMessage(payload: unknown, fallback: string): string {
  if (typeof payload === 'string') return payload.trim() || fallback;
  if (!isRecord(payload)) return fallback;
  if (typeof payload.message === 'string' && payload.message.trim()) return payload.message;
  if (typeof payload.detail === 'string' && payload.detail.trim()) return payload.detail;
  if (isRecord(payload.error) && typeof payload.error.message === 'string' && payload.error.message.trim()) {
    return payload.error.message;
  }
  return fallback;
}

/* ============================================================
 * SSE-PARSING (unverändert, aber gekürzt)
 * ============================================================ */

type RawSseEvent = { event: string; id: string | null; data: string };
type ChatStreamEventType =
  | 'start'
  | 'token'
  | 'message'
  | 'reasoning'
  | 'tool_call'
  | 'tool_result'
  | 'usage'
  | 'complete'
  | 'error'
  | 'heartbeat';
type ChatStreamEnvelope = {
  schema_version?: unknown;
  event?: unknown;
  sequence?: unknown;
  request_id?: unknown;
  conversation_id?: unknown;
  message_id?: unknown;
  data?: unknown;
};
type ParsedChatStreamEvent = {
  schemaVersion: string | null;
  type: string;
  sequence: number | null;
  requestId: string | null;
  conversationId: string | null;
  messageId: string | null;
  payload: unknown;
};

const KNOWN_STREAM_EVENT_TYPES = new Set<ChatStreamEventType>([
  'start',
  'token',
  'message',
  'reasoning',
  'tool_call',
  'tool_result',
  'usage',
  'complete',
  'error',
  'heartbeat',
]);

function parseSseEvent(chunk: string): RawSseEvent | null {
  let event = 'message';
  let id: string | null = null;
  const dataLines: string[] = [];
  for (const line of chunk.split('\n')) {
    if (!line || line.startsWith(':')) continue;
    const separatorIndex = line.indexOf(':');
    let field: string, fieldValue: string;
    if (separatorIndex === -1) {
      field = line;
      fieldValue = '';
    } else {
      field = line.slice(0, separatorIndex);
      fieldValue = line.slice(separatorIndex + 1);
      if (fieldValue.startsWith(' ')) fieldValue = fieldValue.slice(1);
    }
    switch (field) {
      case 'event':
        event = fieldValue || 'message';
        break;
      case 'id':
        id = fieldValue || null;
        break;
      case 'data':
        dataLines.push(fieldValue);
        break;
    }
  }
  if (dataLines.length === 0) return null;
  return { event, id, data: dataLines.join('\n') };
}

function parseChatStreamEvent(rawEvent: RawSseEvent): ParsedChatStreamEvent {
  let parsed: unknown;
  try {
    parsed = JSON.parse(rawEvent.data);
  } catch (error) {
    throw new Error(`Das SSE-Ereignis "${rawEvent.event}" enthält kein gültiges JSON.`, { cause: error });
  }
  if (!isRecord(parsed)) {
    throw new Error(`Das SSE-Ereignis "${rawEvent.event}" enthält keinen gültigen Ereignisumschlag.`);
  }
  const envelope = parsed as ChatStreamEnvelope;
  const envelopeEvent = asOptionalString(envelope.event);
  const schemaVersion = asOptionalString(envelope.schema_version);
  const eventType = envelopeEvent ?? rawEvent.event;
  return {
    schemaVersion,
    type: eventType,
    sequence: asOptionalSequence(envelope.sequence) ?? asOptionalSequence(rawEvent.id),
    requestId: asOptionalString(envelope.request_id),
    conversationId: asOptionalString(envelope.conversation_id),
    messageId: asOptionalString(envelope.message_id),
    payload: envelope.data,
  };
}

/* ============================================================
 * HAUPTKOMPONENTE
 * ============================================================ */

export function GenericChatView({ title, hierarchyNodeId, hierarchyNodeType }: GenericChatViewProps) {
  // State
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [requestStatus, setRequestStatus] = useState<ChatRequestStatus>('idle');
  const [error, setError] = useState<string | null>(null);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [mentionCandidates, setMentionCandidates] = useState<MentionCandidate[]>([]);
  const [selectedMentions, setSelectedMentions] = useState<MentionCandidate[]>([]);
  const [mentionQuery, setMentionQuery] = useState<string | null>(null);
  const [aiResponseOnMentions, setAiResponseOnMentions] = useState(false);
  const [deliveryReceiptsEnabled, setDeliveryReceiptsEnabled] = useState(true);
  const [replyTo, setReplyTo] = useState<ChatMessage | null>(null);

  // Refs
  const abortControllerRef = useRef<AbortController | null>(null);
  const streamHandleRef = useRef<ApiStreamHandle | null>(null);
  const historyFetchControllerRef = useRef<AbortController | null>(null);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);
  const historyGenerationRef = useRef(0);

  // Hooks
  const appState = useAppStoreState();
  const { fetchHistory } = useChatHistory();

  const loading = requestStatus === 'connecting' || requestStatus === 'streaming';

  useEffect(() => {
    void loadUserPreferences()
      .then((preferences) => {
        if (preferences) {
          setAiResponseOnMentions(preferences.aiResponseOnMentions);
          setDeliveryReceiptsEnabled(preferences.deliveryReceiptsEnabled);
        }
      })
      .catch(() => undefined);
  }, []);

  useEffect(() => {
    if (mentionQuery === null) {
      setMentionCandidates([]);
      return;
    }
    let active = true;
    const timeout = window.setTimeout(() => {
      void loadMentionCandidates(mentionQuery, hierarchyNodeId)
        .then((candidates) => {
          if (active) setMentionCandidates(candidates);
        })
        .catch(() => {
          if (active) setMentionCandidates([]);
        });
    }, 120);
    return () => {
      active = false;
      window.clearTimeout(timeout);
    };
  }, [hierarchyNodeId, mentionQuery]);

  // --- LOCAL STORAGE HELPERS ---
  const CONVERSATION_MAP_KEY = 'chat:conversation_map';
  function loadConversationMap(): Record<string, string> {
    try {
      const raw = window.localStorage.getItem(CONVERSATION_MAP_KEY);
      if (!raw) return {};
      const parsed = JSON.parse(raw);
      if (isRecord(parsed)) return parsed as Record<string, string>;
    } catch {}
    return {};
  }
  function saveConversationForNode(nodeId: string, convId: string | null): void {
    try {
      const map = loadConversationMap();
      if (convId === null) delete map[nodeId];
      else map[nodeId] = convId;
      window.localStorage.setItem(CONVERSATION_MAP_KEY, JSON.stringify(map));
    } catch {}
  }
  function persistAndSetConversationId(convId: string | null): void {
    setConversationId(convId);
    try {
      saveConversationForNode(hierarchyNodeId, convId);
    } catch {}
  }

  // --- HISTORY MAPPING ---
  function mapHistoryMessageToChatMessage(m: any, convId: string | null): ChatMessage {
    return {
      id: String(m.id),
      role: (m.role as ChatRole) ?? 'assistant',
      content: typeof m.content === 'string' ? m.content : typeof m.text === 'string' ? m.text : '',
      timestamp: m.created_at ? Date.parse(m.created_at) : Date.now(),
      status: (m.status === 'pending' ? 'pending' : 'completed') as ChatMessageStatus,
      conversationId: convId ?? undefined,
      serverMessageId: String(m.id),
      parentMessageId: typeof m.parent_message_id === 'string' ? m.parent_message_id : undefined,
      directedToUser: Array.isArray(m.ui_context?.mentions) && m.ui_context.mentions.length > 0,
      authorName:
        typeof m.ui_context?.assistant_display_name === 'string'
          ? m.ui_context.assistant_display_name
          : undefined,
    };
  }

  // --- LEBENSZYKLUS ---
  useEffect(() => {
    setInput('');
    setError(null);
    setRequestStatus('idle');

    historyFetchControllerRef.current?.abort();
    const controller = new AbortController();
    historyFetchControllerRef.current = controller;
    const generation = ++historyGenerationRef.current;

    (async () => {
      try {
        let canonicalConvId: string | null = null;
        // Try in-memory store first
        try {
          const state = appState;
          const selected = selectSelectedNode(state);
          if (selected && selected.id === hierarchyNodeId && isRecord(selected.metadata)) {
            const md = selected.metadata as Record<string, unknown>;
            if (typeof md.entity_type === 'string' && md.entity_type === 'conversation' && typeof md.entity_id === 'string') {
              canonicalConvId = md.entity_id;
            }
          }
        } catch {}

        // Fallback: localStorage mapping
        if (!canonicalConvId) {
          const map = loadConversationMap();
          if (map[hierarchyNodeId]) {
            setConversationId(map[hierarchyNodeId]);
          } else {
            setConversationId(null);
          }
        }

        // Fallback: fetch node from backend
        if (!canonicalConvId) {
          try {
            const node = await apiGet<any>(`/hierarchy/${encodeURIComponent(hierarchyNodeId)}`, {
              signal: controller.signal,
            });
            if (isRecord(node?.metadata)) {
              const meta = node.metadata as Record<string, unknown>;
              if (typeof meta.entity_type === 'string' && meta.entity_type === 'conversation') {
                const candidate = meta.entity_id as unknown;
                if (typeof candidate === 'string' && candidate.trim()) {
                  canonicalConvId = candidate;
                }
              }
            }
          } catch {}
        }

        const map = loadConversationMap();
        const convIdToUse = canonicalConvId ?? map[hierarchyNodeId] ?? null;

        if (!convIdToUse) {
          persistAndSetConversationId(null);
          setMessages([]);
          return;
        }

        persistAndSetConversationId(convIdToUse);
        const history = await fetchHistory(convIdToUse);
        if (controller.signal.aborted) return;
        if (generation !== historyGenerationRef.current) return;

        if (history && Array.isArray(history)) {
          const mapped = history.map((m) => mapHistoryMessageToChatMessage(m, convIdToUse));
          setMessages(mapped);
        } else {
          setMessages([]);
        }
      } catch (err) {
        if (controller.signal.aborted) return;
        console.error('[GenericChatView] load-history-failed', err);
      }
    })();

    return () => {
      streamHandleRef.current?.cancel();
      streamHandleRef.current?.dispose();
      streamHandleRef.current = null;
      abortControllerRef.current?.abort();
      abortControllerRef.current = null;
      historyFetchControllerRef.current?.abort();
      historyFetchControllerRef.current = null;
    };
  }, [hierarchyNodeId, title, appState.hierarchyTree, appState.selectedNodeId]);

  // Auto-scroll
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
  }, [messages]);

  // Auto-resize textarea
  useEffect(() => {
    const textarea = textareaRef.current;
    if (!textarea) return;
    textarea.style.height = 'auto';
    textarea.style.height = `${Math.min(textarea.scrollHeight, MAX_INPUT_HEIGHT)}px`;
  }, [input]);

  // --- HELPER FUNCTIONS FOR MESSAGE STATE ---
  function updateAssistantMessage(assistantMessageId: string, update: Partial<ChatMessage>): void {
    setMessages((prev) =>
      prev.map((msg) => (msg.id === assistantMessageId ? { ...msg, ...update } : msg))
    );
  }

  function appendAssistantContent(
    assistantMessageId: string,
    content: string,
    metadata: {
      requestId?: string | null;
      conversationId?: string | null;
      messageId?: string | null;
    } = {}
  ): void {
    if (!content) return;
    setMessages((prev) =>
      prev.map((msg) => {
        if (msg.id !== assistantMessageId) return msg;
        return {
          ...msg,
          content: msg.content + content,
          status: 'streaming',
          requestId: metadata.requestId ?? msg.requestId,
          conversationId: metadata.conversationId ?? msg.conversationId,
          serverMessageId: metadata.messageId ?? msg.serverMessageId,
        };
      })
    );
  }

  function setAssistantContent(
    assistantMessageId: string,
    content: string,
    metadata: {
      requestId?: string | null;
      conversationId?: string | null;
      messageId?: string | null;
      status?: ChatMessageStatus;
    } = {}
  ): void {
    setMessages((prev) =>
      prev.map((msg) => {
        if (msg.id !== assistantMessageId) return msg;
        return {
          ...msg,
          content,
          status: metadata.status ?? 'streaming',
          requestId: metadata.requestId ?? msg.requestId,
          conversationId: metadata.conversationId ?? msg.conversationId,
          serverMessageId: metadata.messageId ?? msg.serverMessageId,
        };
      })
    );
  }

  // --- STREAM PROCESSING (unverändert, intern gekürzt) ---
  async function processSseStream(
    streamHandle: ApiStreamHandle,
    assistantMessageId: string,
    abortSignal: AbortSignal,
    streamGeneration: number
  ): Promise<void> {
    const response = streamHandle.response;
    if (!response.body) throw new Error('Der Server hat keinen lesbaren Datenstrom geliefert.');

    const headerRequestId = streamHandle.requestId ?? response.headers.get('x-request-id');
    const reader = response.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let buffer = '';
    let completeReceived = false;
    let errorReceived = false;
    let processedEventCount = 0;
    let receivedCharacterCount = 0;
    let lastSequence: number | null = null;

    async function processChunk(chunk: string): Promise<void> {
      const rawEvent = parseSseEvent(chunk);
      if (!rawEvent) return;

      const streamEvent = parseChatStreamEvent(rawEvent);
      if (streamEvent.schemaVersion !== CHAT_STREAM_SCHEMA_VERSION) {
        throw new Error(
          `Der Server verwendet eine nicht unterstützte Chat-Stream-Version. Erwartet: ${CHAT_STREAM_SCHEMA_VERSION}, erhalten: ${streamEvent.schemaVersion ?? 'nicht angegeben'}.`
        );
      }
      if (streamEvent.sequence !== null) {
        if (lastSequence !== null && streamEvent.sequence < lastSequence) {
          throw new Error('Der Chat-Stream enthält eine ungültige Ereignisreihenfolge.');
        }
        if (lastSequence !== null && streamEvent.sequence === lastSequence) {
          return;
        }
        lastSequence = streamEvent.sequence;
      }
      processedEventCount += 1;

      if (!KNOWN_STREAM_EVENT_TYPES.has(streamEvent.type as ChatStreamEventType)) {
        return;
      }

      const eventType = streamEvent.type as ChatStreamEventType;
      const requestId = streamEvent.requestId ?? headerRequestId;

      switch (eventType) {
        case 'start': {
          setRequestStatus('streaming');
          if (streamEvent.conversationId) persistAndSetConversationId(streamEvent.conversationId);
          updateAssistantMessage(assistantMessageId, {
            status: 'streaming',
            requestId: requestId ?? undefined,
            conversationId: streamEvent.conversationId ?? undefined,
            serverMessageId: streamEvent.messageId ?? undefined,
          });
          break;
        }
        case 'token': {
          const content = extractContentFromPayload(streamEvent.payload);
          if (!content) return;
          receivedCharacterCount += content.length;
          appendAssistantContent(assistantMessageId, content, {
            requestId,
            conversationId: streamEvent.conversationId,
            messageId: streamEvent.messageId,
          });
          break;
        }
        case 'message': {
          const content = extractContentFromPayload(streamEvent.payload);
          if (!content) return;
          receivedCharacterCount = content.length;
          setAssistantContent(assistantMessageId, content, {
            requestId,
            conversationId: streamEvent.conversationId,
            messageId: streamEvent.messageId,
            status: 'streaming',
          });
          break;
        }
        case 'complete': {
          completeReceived = true;
          const finalContent = extractContentFromPayload(streamEvent.payload);
          if (finalContent) {
            receivedCharacterCount = finalContent.length;
            setAssistantContent(assistantMessageId, finalContent, {
              requestId,
              conversationId: streamEvent.conversationId,
              messageId: streamEvent.messageId,
              status: 'completed',
            });
          } else {
            updateAssistantMessage(assistantMessageId, {
              status: 'completed',
              requestId: requestId ?? undefined,
              conversationId: streamEvent.conversationId ?? undefined,
              serverMessageId: streamEvent.messageId ?? undefined,
            });
          }
          if (streamEvent.conversationId) persistAndSetConversationId(streamEvent.conversationId);

          // Reload history after complete
          if (streamEvent.conversationId) {
            try {
              const serverHistory = await fetchHistory(streamEvent.conversationId);
              if (abortSignal.aborted) return;
              if (serverHistory && Array.isArray(serverHistory)) {
                const mappedServer = serverHistory.map((m) =>
                  mapHistoryMessageToChatMessage(m, streamEvent.conversationId)
                );
                if (historyGenerationRef.current === streamGeneration) {
                  setMessages(mappedServer);
                }
              }
            } catch {}
          }
          break;
        }
        case 'error': {
          errorReceived = true;
          const message = extractErrorMessage(streamEvent.payload, 'Beim Verarbeiten der Nachricht ist ein Fehler aufgetreten.');
          throw new Error(message);
        }
        case 'heartbeat':
        case 'reasoning':
        case 'tool_call':
        case 'tool_result':
        case 'usage':
          // ignore metadata events
          break;
      }
    }

    try {
      while (true) {
        if (abortSignal.aborted) throw new DOMException('Die Anfrage wurde abgebrochen.', 'AbortError');
        const { value, done } = await reader.read();
        if (done) {
          buffer += decoder.decode();
          break;
        }
        buffer += decoder.decode(value, { stream: true });
        buffer = normalizeSseBuffer(buffer);
        const chunks = buffer.split('\n\n');
        buffer = chunks.pop() ?? '';
        for (const chunk of chunks) {
          await processChunk(chunk);
        }
      }
      const remainingChunk = normalizeSseBuffer(buffer).trim();
      if (remainingChunk) {
        await processChunk(remainingChunk);
      }
    } finally {
      try {
        reader.releaseLock();
      } catch {}
    }

    if (!completeReceived && !errorReceived && !abortSignal.aborted) {
      throw new Error('Die Verbindung wurde beendet, bevor der Server den Chat-Stream ordnungsgemäß abgeschlossen hat.');
    }
  }

  // --- SUBMIT ---
  async function submit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    if (loading) return;
    if (!hierarchyNodeId || !String(hierarchyNodeId).trim()) {
      setError('Bitte wählen oder erstellen Sie zuerst einen Chat.');
      return;
    }

    let prompt: string;
    try {
      prompt = validatePrompt(input);
    } catch (validationError) {
      const message = validationError instanceof Error ? validationError.message : 'Die Nachricht ist ungültig.';
      setError(message);
      return;
    }

    if (hierarchyNodeType !== 'chat') {
      setError('Bitte wählen oder erstellen Sie zuerst einen Chat.');
      return;
    }

    const userMessageId = createMessageId();
    const assistantMessageId = createMessageId();
    const submittedAt = Date.now();
    const activeConversationId = conversationId;
    const administratorAutoAnswer = selectedMentions.some(
      (candidate) => candidate.isAdministrator,
    );
    const expectsAiResponse =
      administratorAutoAnswer || selectedMentions.length === 0 || aiResponseOnMentions;

    const userMessage: ChatMessage = {
      id: userMessageId,
      role: 'user',
      content: prompt,
      timestamp: submittedAt,
      status: 'completed',
      conversationId: activeConversationId ?? undefined,
      parentMessageId: replyTo?.serverMessageId ?? replyTo?.id,
      directedToUser: selectedMentions.length > 0,
    };

    const assistantMessage: ChatMessage = {
      id: assistantMessageId,
      role: 'assistant',
      content: '',
      timestamp: submittedAt,
      status: 'pending',
      conversationId: activeConversationId ?? undefined,
      authorName: administratorAutoAnswer ? 'Administrator' : undefined,
      parentMessageId: replyTo?.serverMessageId ?? replyTo?.id,
    };

    const requestPayload: ChatRequestPayload = {
      message: prompt,
      conversation_id: activeConversationId,
      parent_message_id: replyTo?.serverMessageId ?? replyTo?.id ?? null,
      hierarchy_node_id: hierarchyNodeId,
      model_id: null,
      tool_ids: [],
      mentions: selectedMentions.map((candidate) => ({ user_id: candidate.userId })),
      ai_response: selectedMentions.length > 0 ? aiResponseOnMentions : null,
      metadata: {
        client: 'kernschmied-web',
        client_message_id: userMessageId,
        client_assistant_message_id: assistantMessageId,
        submitted_at: new Date(submittedAt).toISOString(),
      },
    };

    try {
      validateChatRequest(requestPayload);
    } catch (validationError) {
      const message = validationError instanceof Error ? validationError.message : 'Die Chat-Anfrage ist ungültig.';
      setError(message);
      return;
    }

    setMessages((prev) => [...prev, userMessage, assistantMessage]);
    setInput('');
    setSelectedMentions([]);
    setReplyTo(null);
    setMentionQuery(null);
    setError(null);
    setRequestStatus('connecting');

    const abortController = new AbortController();
    abortControllerRef.current = abortController;

    let streamHandle: ApiStreamHandle | null = null;
    try {
      streamHandle = await apiPostStream(CHAT_STREAM_PATH, requestPayload, {
        signal: abortController.signal,
        expectedContentType: 'text/event-stream',
      });
      streamHandleRef.current = streamHandle;
      setRequestStatus('streaming');
      updateAssistantMessage(assistantMessageId, {
        requestId: streamHandle.requestId,
        status: 'streaming',
      });

      const streamGeneration = historyGenerationRef.current;
      await processSseStream(streamHandle, assistantMessageId, abortController.signal, streamGeneration);

      setMessages((prev) =>
        prev.flatMap((msg) => {
          if (msg.id !== assistantMessageId) return msg;
          if (msg.content.trim() === '') {
            if (!expectsAiResponse) return [];
            return { ...msg, content: 'Der Server hat keine Antwort geliefert.', status: 'completed' };
          }
          return { ...msg, status: 'completed' };
        })
      );
      setRequestStatus('completed');
    } catch (caughtError) {
      const requestWasAborted =
        abortController.signal.aborted ||
        isAbortError(caughtError) ||
        (caughtError instanceof ApiError && caughtError.code === 'request_aborted');

      if (requestWasAborted) {
        setRequestStatus('cancelled');
        setAssistantContent(assistantMessageId, 'Die Antwort wurde abgebrochen.', { status: 'cancelled' });
        return;
      }

      const message = formatRequestError(caughtError);
      setRequestStatus('failed');
      setError(message);
      setAssistantContent(assistantMessageId, `Fehler: ${message}`, {
        status: 'failed',
        requestId: caughtError instanceof ApiError ? caughtError.requestId : null,
      });
    } finally {
      streamHandle?.dispose();
      if (streamHandleRef.current === streamHandle) streamHandleRef.current = null;
      if (abortControllerRef.current === abortController) abortControllerRef.current = null;
    }
  }

  function stopGeneration(): void {
    streamHandleRef.current?.cancel();
    abortControllerRef.current?.abort(new DOMException('Die Antwort wurde vom Benutzer abgebrochen.', 'AbortError'));
  }

  function handleInputChange(value: string): void {
    setInput(value);
    setSelectedMentions((current) =>
      current.filter((candidate) => value.includes(`@${candidate.username}`)),
    );
    const match = value.match(/(?:^|\s)@([A-Za-z0-9._-]*)$/);
    setMentionQuery(match ? match[1] : null);
  }

  function selectMention(candidate: MentionCandidate): void {
    setInput((current) =>
      current.replace(/(^|\s)@[A-Za-z0-9._-]*$/, `$1@${candidate.username} `),
    );
    setSelectedMentions((current) =>
      current.some((item) => item.userId === candidate.userId)
        ? current
        : [...current, candidate],
    );
    setMentionQuery(null);
    textareaRef.current?.focus();
  }

  function handleInputKeyDown(event: KeyboardEvent<HTMLTextAreaElement>): void {
    if (event.key === 'Escape' && loading) {
      event.preventDefault();
      stopGeneration();
      return;
    }
    if (event.key === 'Enter' && !event.shiftKey && !event.nativeEvent.isComposing) {
      event.preventDefault();
      if (!loading && input.trim()) {
        event.currentTarget.form?.requestSubmit();
      }
    }
  }

  // --- RENDER ---
  const activeAssistantMessage = [...messages]
    .reverse()
    .find((msg) => msg.role === 'assistant' && (msg.status === 'pending' || msg.status === 'streaming'));
  const showTypingIndicator = loading && Boolean(activeAssistantMessage) && !activeAssistantMessage?.content;
  const accessibleStatus = getAccessibleRequestStatus(requestStatus);
  const cfg = getNodeTypeConfig(hierarchyNodeType);

  return (
    <WorkspaceLayout
      icon={<IconBadge icon={<DynamicIcon name={cfg.icon ?? 'MessageSquare'} />} size={cfg.defaultSize} variant={cfg.variant} />}
      title={`Chat: ${title}`}
      background="slate"
    >
      <div className="flex h-full flex-col">
        <p className="sr-only" aria-live="polite">
          {accessibleStatus}
        </p>

        {/* Nachrichtenbereich – scrollt */}
        <div
          className="flex-1 overflow-y-auto overscroll-contain bg-white/50 dark:bg-slate-950/30"
          aria-live="polite"
          aria-busy={loading}
        >
          <div className="mx-auto max-w-4xl px-4 py-6 sm:px-6 lg:px-8">
            {messages.length === 0 ? (
              <div className="flex min-h-[60vh] flex-col items-center justify-center text-center">
                <div className="mb-4">
                  <IconBadge
                    icon={<MessageCircle />}
                    size="lg"
                    variant="default"
                    className="shadow-sm border-border-soft bg-white/70 dark:border-white/10 dark:bg-slate-800/60"
                  />
                </div>
                <h3 className="text-lg font-medium text-text-soft dark:text-gray-300">Noch keine Nachrichten</h3>
                <p className="mt-1 text-sm text-text-muted dark:text-gray-400">Schreibe eine Nachricht, um diesen Chat zu beginnen.</p>
              </div>
            ) : (
              <div className="space-y-6">
                {messages.map((message) => {
                  const isUser = message.role === 'user';
                  const isSystem = message.role === 'system';
                  const parentMessage = message.parentMessageId
                    ? messages.find((candidate) => (candidate.serverMessageId ?? candidate.id) === message.parentMessageId)
                    : undefined;
                  const isEmptyAssistant = !isUser && !message.content && (message.status === 'pending' || message.status === 'streaming');
                  if (isSystem || isEmptyAssistant) return null;

                  return (
                    <article
                      key={message.id}
                      className={`flex items-start gap-3 ${isUser ? 'flex-row-reverse' : 'flex-row'} ${message.parentMessageId ? 'ml-8 w-[calc(100%-2rem)] border-l-4 border-cyan-500/70 pl-3' : 'w-full'}`}
                      data-message-id={message.id}
                      data-message-status={message.status}
                    >
                      <IconBadge
                        icon={<span className="text-xs font-bold uppercase">{getInitials(message.role)}</span>}
                        size="sm"
                        variant={isUser ? 'primary' : 'secondary'}
                        className="shrink-0 ring-1 ring-primary/15 dark:ring-primary/25"
                      />

                      <div
                        className={`min-w-0 rounded-2xl px-4 py-3 shadow-sm ${
                          isUser
                            ? 'max-w-[85%] bg-primary text-white dark:bg-primary-dark'
                            : 'w-full max-w-6xl border border-border-soft bg-white/90 backdrop-blur-sm dark:border-white/10 dark:bg-slate-800/80'
                        }`}
                      >
                        <div className="flex items-center justify-between gap-4">
                          <span className={`text-xs font-semibold ${isUser ? 'text-white/80' : 'text-text-muted dark:text-gray-400'}`}>
                            {isUser ? 'Du' : (message.authorName ? `${message.authorName} · KI` : 'KI-Assistent')}
                          </span>
                          <time
                            dateTime={new Date(message.timestamp).toISOString()}
                            className={`shrink-0 text-xs ${isUser ? 'text-white/60' : 'text-text-subtle dark:text-gray-500'}`}
                          >
                            {formatTime(message.timestamp)}
                          </time>
                        </div>
                        {message.parentMessageId ? (
                          <div className={`mt-2 rounded border-l-2 px-2 py-1 text-xs ${isUser ? 'border-white/50 bg-white/10 text-white/80' : 'border-cyan-500 bg-cyan-50 text-cyan-900 dark:bg-cyan-950/30 dark:text-cyan-200'}`}>
                            Nebenchat als Antwort auf: {parentMessage?.content.slice(0, 90) ?? 'vorherige Nachricht'}
                          </div>
                        ) : null}
                        <p
                          className={`mt-1 whitespace-pre-wrap wrap-break-words text-sm leading-6 ${
                            isUser ? 'text-white' : 'text-text dark:text-gray-100'
                          }`}
                        >
                          {message.content}
                        </p>
                        <div className={`mt-2 flex items-center justify-between gap-3 text-[11px] ${isUser ? 'text-white/70' : 'text-text-muted'}`}>
                          {deliveryReceiptsEnabled ? <span>{getDeliveryStatus(message)}</span> : <span />}
                          <button
                            type="button"
                            onClick={() => setReplyTo(message)}
                            className="inline-flex items-center gap-1 rounded px-1.5 py-0.5 hover:bg-black/10"
                            aria-label="Auf diese Nachricht antworten"
                          >
                            <CornerUpLeft className="h-3.5 w-3.5" /> Antworten
                          </button>
                        </div>
                      </div>
                    </article>
                  );
                })}

                {showTypingIndicator && (
                  <div className="flex w-full items-start gap-3 animate-fade-in">
                    <IconBadge
                      icon={<span className="text-xs font-bold uppercase">KI</span>}
                      size="sm"
                      variant="secondary"
                      className="shrink-0 ring-1 ring-secondary/15 dark:ring-secondary/25"
                    />
                    <div className="rounded-2xl border border-border-soft bg-white/90 px-4 py-3 shadow-sm backdrop-blur-sm dark:border-white/10 dark:bg-slate-800/80">
                      <div className="flex items-center gap-1">
                        <span className="h-2 w-2 animate-pulse rounded-full bg-primary/60" />
                        <span className="h-2 w-2 animate-pulse rounded-full bg-primary/60 animation-delay-200" />
                        <span className="h-2 w-2 animate-pulse rounded-full bg-primary/60 animation-delay-400" />
                        <span className="ml-2 text-sm text-text-muted dark:text-gray-400">Antwort wird erstellt …</span>
                      </div>
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} aria-hidden="true" />
              </div>
            )}
          </div>
        </div>

        {/* Fehleranzeige (fixiert, nur wenn vorhanden) */}
        {error && (
          <div
            className="shrink-0 border-t border-danger/20 bg-danger-soft px-4 py-2.5 text-sm text-danger dark:bg-danger/10 sm:px-6 lg:px-8"
            role="alert"
          >
            <div className="mx-auto max-w-4xl">
              <span className="font-medium">Fehler:</span> {error}
            </div>
          </div>
        )}

        {/* Eingabebereich (fixiert am unteren Rand) */}
        <form
          onSubmit={submit}
          className="shrink-0 border-t border-border bg-white/85 px-4 py-3 backdrop-blur-md dark:border-white/10 dark:bg-slate-900/75 sm:px-6 lg:px-8"
        >
          <div className="mx-auto max-w-4xl">
            {replyTo ? (
              <div className="mb-2 flex items-center gap-2 border-l-4 border-cyan-500 bg-cyan-50 px-3 py-2 text-xs text-cyan-950 dark:bg-cyan-950/30 dark:text-cyan-100">
                <CornerUpLeft className="h-4 w-4 shrink-0" />
                <span className="min-w-0 flex-1 truncate">Nebenchat zu: {replyTo.content}</span>
                <button type="button" onClick={() => setReplyTo(null)} className="rounded p-1 hover:bg-cyan-100 dark:hover:bg-cyan-900" aria-label="Antwortbezug entfernen">
                  <X className="h-4 w-4" />
                </button>
              </div>
            ) : null}
            <div className="flex w-full items-end gap-2">
              <div className="relative min-w-0 flex-1">
                <label htmlFor="chat-message-input" className="sr-only">
                  Nachricht
                </label>
                <textarea
                  ref={textareaRef}
                  id="chat-message-input"
                  rows={1}
                  className="max-h-48 min-h-11 w-full resize-none overflow-y-auto rounded-xl border border-border-soft bg-surface-muted px-4 py-2.5 text-sm leading-6 text-text outline-none transition placeholder:text-text-subtle focus:border-primary focus:ring-4 focus:ring-primary-soft disabled:cursor-not-allowed disabled:opacity-60 dark:border-white/10 dark:bg-slate-800/50 dark:text-white dark:placeholder:text-gray-500 dark:focus:ring-primary/20"
                  value={input}
                  onChange={(event) => handleInputChange(event.target.value)}
                  onKeyDown={handleInputKeyDown}
                  placeholder="Nachricht eingeben … Mit @ Benutzer anfragen"
                  autoComplete="off"
                  disabled={loading}
                  maxLength={MAX_MESSAGE_LENGTH}
                />
                {mentionQuery !== null && mentionCandidates.length > 0 ? (
                  <div
                    className="absolute bottom-full z-30 mb-2 max-h-56 w-full overflow-y-auto rounded-lg border border-border bg-white p-1 shadow-xl dark:border-white/10 dark:bg-slate-800"
                    role="listbox"
                    aria-label="Benutzer erwähnen"
                  >
                    {mentionCandidates.map((candidate) => (
                      <button
                        key={candidate.userId}
                        type="button"
                        role="option"
                        aria-selected="false"
                        className="flex w-full items-center gap-3 rounded-md px-3 py-2 text-left hover:bg-surface-hover dark:hover:bg-slate-700"
                        onMouseDown={(event) => event.preventDefault()}
                        onClick={() => selectMention(candidate)}
                      >
                        <span
                          className={`h-2.5 w-2.5 shrink-0 rounded-full ${candidate.online ? 'bg-emerald-500' : 'bg-gray-300 dark:bg-gray-600'}`}
                          aria-label={candidate.online ? 'Online' : 'Offline'}
                        />
                        <span className="min-w-0">
                          <span className="block truncate text-sm font-medium">{candidate.displayName}</span>
                          <span className="block truncate text-xs text-text-muted">@{candidate.username}</span>
                        </span>
                      </button>
                    ))}
                  </div>
                ) : null}
              </div>

              {loading ? (
                <button
                  type="button"
                  className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl border border-border-soft bg-surface text-text-soft shadow-sm transition hover:bg-surface-hover hover:text-text focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 dark:border-white/10 dark:bg-slate-800/70 dark:text-gray-300 dark:hover:bg-slate-700/70 dark:hover:text-white dark:focus-visible:ring-offset-slate-900"
                  onClick={stopGeneration}
                  aria-label="Antwort abbrechen"
                  title="Antwort abbrechen"
                >
                  <IconBadge icon={<Square />} size="sm" variant="default" />
                </button>
              ) : (
                <button
                  type="submit"
                  className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-primary text-white shadow-glow transition hover:bg-primary-hover hover:shadow-primary-glow focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-40 dark:bg-primary-dark dark:hover:bg-primary-dark-hover dark:focus-visible:ring-offset-slate-900"
                  disabled={!input.trim() || !hierarchyNodeId || !String(hierarchyNodeId).trim()}
                  aria-label="Nachricht senden"
                  title="Nachricht senden"
                >
                  <IconBadge icon={<Send />} size="sm" variant="default" />
                </button>
              )}
            </div>

            <div className="mt-2 flex items-center justify-between gap-4 text-xs text-text-muted dark:text-gray-500">
              <p className="truncate">Enter sendet · Shift+Enter neue Zeile · Escape bricht ab</p>
              <span className="shrink-0 tabular-nums">
                {input.length.toLocaleString('de-DE')}/{MAX_MESSAGE_LENGTH.toLocaleString('de-DE')}
              </span>
            </div>

            {selectedMentions.length > 0 ? (
              <label className="mt-2 flex items-center gap-2 text-xs text-text-soft dark:text-gray-300">
                <input
                  type="checkbox"
                  checked={aiResponseOnMentions}
                  onChange={(event) => setAiResponseOnMentions(event.target.checked)}
                />
                KI antwortet zusätzlich
                <span className="text-text-muted">
                  ({selectedMentions.length} Benutzer angefragt)
                </span>
              </label>
            ) : null}

            {/* Widget-Bar (fixiert) */}
            <ChatWidgetBar nodeId={hierarchyNodeId} />
          </div>
        </form>
      </div>
    </WorkspaceLayout>
  );
}

/* ============================================================
 * CHAT-WIDGET-BAR (mit verbessertem Popover)
 * ============================================================ */

function ChatWidgetBar({ nodeId }: { nodeId: string }) {
  const { widgets, isLoading } = useEffectiveWidgets(nodeId);
  const [openWidgetId, setOpenWidgetId] = useState<string | null>(null);
  const [popoverPosition, setPopoverPosition] = useState<{ top: number; left: number } | null>(null);
  const buttonRefs = useRef<Map<string, HTMLButtonElement>>(new Map());

  const chatWidgets = (widgets || []).filter((w) => {
    const declared = (w.componentType ?? (w.metadata && (w.metadata.component_type as string | undefined))) as string | undefined;
    return declared ? declared.startsWith('chat') || declared.startsWith('chat_') : false;
  });

  // Schließen bei Klick außerhalb
  useEffect(() => {
    const onClickOutside = (e: MouseEvent) => {
      if (openWidgetId) {
        const target = e.target as Node;
        const button = buttonRefs.current.get(openWidgetId);
        const popover = document.getElementById(`widget-popover-${openWidgetId}`);
        if (button && !button.contains(target) && popover && !popover.contains(target)) {
          setOpenWidgetId(null);
          setPopoverPosition(null);
        }
      }
    };
    document.addEventListener('mousedown', onClickOutside);
    return () => document.removeEventListener('mousedown', onClickOutside);
  }, [openWidgetId]);

  if (!chatWidgets || chatWidgets.length === 0) return null;

  function handleToggle(widgetId: string, buttonElement: HTMLButtonElement) {
    if (openWidgetId === widgetId) {
      setOpenWidgetId(null);
      setPopoverPosition(null);
      return;
    }
    const rect = buttonElement.getBoundingClientRect();
    setPopoverPosition({
      top: rect.bottom + 8,
      left: rect.left,
    });
    setOpenWidgetId(widgetId);
  }

  return (
    <div className="mt-3 flex items-center gap-2">
      {chatWidgets.map((w) => {
        const iconName = w.icon ?? undefined;
        const isOpen = openWidgetId === w.id;
        return (
          <button
            key={w.id}
            ref={(el) => {
              if (el) buttonRefs.current.set(w.id, el);
              else buttonRefs.current.delete(w.id);
            }}
            type="button"
            title={w.label ?? w.name}
            className={`flex h-9 w-9 items-center justify-center rounded-lg border transition ${
              isOpen
                ? 'border-primary bg-primary-soft dark:border-primary dark:bg-primary/20'
                : 'border-border bg-white hover:bg-surface-hover dark:border-white/10 dark:bg-slate-800 dark:hover:bg-slate-700'
            }`}
            onClick={(e) => handleToggle(w.id, e.currentTarget)}
          >
            <IconBadge
              icon={
                iconName ? (
                  <DynamicIcon name={iconName} />
                ) : (
                  <span className="text-xs font-bold uppercase">{(w.label ?? w.name ?? '').slice(0, 1)}</span>
                )
              }
              size="sm"
              variant={isOpen ? 'primary' : 'default'}
            />
          </button>
        );
      })}

      {/* Popover für geöffnetes Widget */}
      {openWidgetId && popoverPosition && (
        <div
          id={`widget-popover-${openWidgetId}`}
          className="fixed z-50 w-80 max-w-[calc(100vw-2rem)] rounded-xl border border-border-soft bg-white/95 p-4 shadow-xl backdrop-blur-sm dark:border-white/10 dark:bg-slate-900/95 dark:backdrop-blur-sm"
          style={{
            top: popoverPosition.top,
            left: Math.min(popoverPosition.left, window.innerWidth - 340),
            maxHeight: 'calc(100vh - 200px)',
          }}
        >
          <div className="flex items-center justify-between border-b border-border-soft pb-2 dark:border-white/10">
            <h4 className="text-sm font-medium text-text-soft dark:text-gray-200">
              {(() => {
                const w = chatWidgets.find((c) => c.id === openWidgetId);
                return w?.label ?? w?.name ?? 'Widget';
              })()}
            </h4>
            <button
              className="rounded p-1 text-text-muted hover:bg-surface-hover hover:text-text dark:text-gray-500 dark:hover:bg-slate-800 dark:hover:text-gray-300"
              onClick={() => {
                setOpenWidgetId(null);
                setPopoverPosition(null);
              }}
              aria-label="Schließen"
            >
              <IconBadge icon={<span className="text-xs">✕</span>} size="sm" variant="default" />
            </button>
          </div>
          <div className="mt-3 max-h-[40vh] overflow-y-auto text-sm text-text dark:text-gray-200">
            {(() => {
              const widget = chatWidgets.find((c) => c.id === openWidgetId);
              if (!widget) return <div>Widget nicht gefunden.</div>;
              const declared = (widget.componentType ?? (widget.metadata && (widget.metadata.component_type as string | undefined))) as string | undefined;
              const renderer = getWidgetRenderer(declared);
              if (!renderer) return <div>Kein Renderer für dieses Widget installiert.</div>;
              return <div>{renderer(widget, { nodeId })}</div>;
            })()}
          </div>
        </div>
      )}
    </div>
  );
}