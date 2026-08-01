// F:\Kernschmied\frontend\src\components\chat\GenericChatView.tsx

import { useEffect, useRef, useState } from 'react';
import { MessageCircle, Send, Square } from 'lucide-react';

import type { FormEvent, KeyboardEvent } from 'react';

import { ApiError, apiPostStream } from '../../api/client';

import type { ApiStreamHandle } from '../../api/client';

const SOURCE_FILE = 'frontend/src/components/chat/GenericChatView.tsx';

const CHAT_STREAM_PATH = '/chat/stream';

const CHAT_STREAM_SCHEMA_VERSION = '1.0' as const;

const MAX_MESSAGE_LENGTH = 50_000;

const MAX_INPUT_HEIGHT = 192;

/* ============================================================
 * Komponentenverträge
 * ============================================================ */

type GenericChatViewProps = {
  /**
   * Der Titel wird nicht innerhalb der Chatansicht dargestellt.
   *
   * Die sichtbare Überschrift wird zentral durch das AppLayout
   * beziehungsweise den Kontextkopf in App.tsx gerendert.
   *
   * Innerhalb dieser Komponente wird der Titel nur noch für
   * Barrierefreiheit und Entwicklerprotokolle verwendet.
   */
  title: string;

  hierarchyNodeId: string;
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
};

type ChatRequestPayload = {
  message: string;
  conversation_id: string | null;
  hierarchy_node_id: string;
  model_id: string | null;
  tool_ids: string[];
  metadata: Record<string, unknown>;
};

/* ============================================================
 * SSE-Verträge
 * ============================================================ */

type RawSseEvent = {
  event: string;
  id: string | null;
  data: string;
};

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

/* ============================================================
 * Entwicklerinformationen
 * ============================================================ */

type DeveloperLogLevel = 'debug' | 'info' | 'warn' | 'error';

type DeveloperLogContext = Record<string, unknown>;

function logDeveloperStep(
  level: DeveloperLogLevel,
  step: string,
  context: DeveloperLogContext = {},
): void {
  if (!import.meta.env.DEV) {
    return;
  }

  const entry = {
    timestamp: new Date().toISOString(),
    source: SOURCE_FILE,
    area: 'chat-pipeline',
    step,
    ...context,
  };

  switch (level) {
    case 'error':
      console.error('[Kernschmied][ChatPipeline]', entry);
      break;

    case 'warn':
      console.warn('[Kernschmied][ChatPipeline]', entry);
      break;

    case 'info':
      console.info('[Kernschmied][ChatPipeline]', entry);
      break;

    default:
      console.debug('[Kernschmied][ChatPipeline]', entry);
  }
}

/* ============================================================
 * Allgemeine Hilfsfunktionen
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
  if (typeof value !== 'string') {
    return null;
  }

  const normalized = value.trim();

  return normalized || null;
}

function asOptionalSequence(value: unknown): number | null {
  let candidate: number;

  if (typeof value === 'number') {
    candidate = value;
  } else if (typeof value === 'string' && value.trim() !== '') {
    candidate = Number(value);
  } else {
    return null;
  }

  if (!Number.isSafeInteger(candidate) || candidate < 0) {
    return null;
  }

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

  if (!normalized) {
    throw new Error('Die Nachricht darf nicht leer sein.');
  }

  if (normalized.length > MAX_MESSAGE_LENGTH) {
    throw new Error(
      `Die Nachricht darf höchstens ${MAX_MESSAGE_LENGTH.toLocaleString(
        'de-DE',
      )} Zeichen enthalten.`,
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

/* ============================================================
 * SSE-Parsing
 * ============================================================ */

function parseSseEvent(chunk: string): RawSseEvent | null {
  let event = 'message';

  let id: string | null = null;

  const dataLines: string[] = [];

  for (const line of chunk.split('\n')) {
    if (!line || line.startsWith(':')) {
      continue;
    }

    const separatorIndex = line.indexOf(':');

    let field: string;
    let fieldValue: string;

    if (separatorIndex === -1) {
      field = line;
      fieldValue = '';
    } else {
      field = line.slice(0, separatorIndex);
      fieldValue = line.slice(separatorIndex + 1);

      if (fieldValue.startsWith(' ')) {
        fieldValue = fieldValue.slice(1);
      }
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

      default:
        break;
    }
  }

  if (dataLines.length === 0) {
    return null;
  }

  return {
    event,
    id,
    data: dataLines.join('\n'),
  };
}

function parseChatStreamEvent(rawEvent: RawSseEvent): ParsedChatStreamEvent {
  let parsed: unknown;

  try {
    parsed = JSON.parse(rawEvent.data) as unknown;
  } catch (error) {
    throw new Error(`Das SSE-Ereignis "${rawEvent.event}" enthält kein gültiges JSON.`, {
      cause: error,
    });
  }

  if (!isRecord(parsed)) {
    throw new Error(
      `Das SSE-Ereignis "${rawEvent.event}" enthält keinen gültigen Ereignisumschlag.`,
    );
  }

  const envelope = parsed as ChatStreamEnvelope;

  const envelopeEvent = asOptionalString(envelope.event);

  const schemaVersion = asOptionalString(envelope.schema_version);

  const eventType = envelopeEvent ?? rawEvent.event;

  if (envelopeEvent && rawEvent.event !== 'message' && rawEvent.event !== envelopeEvent) {
    logDeveloperStep('warn', 'sse-event-name-mismatch', {
      sseEvent: rawEvent.event,
      envelopeEvent,
    });
  }

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
 * Ereignisinhalte
 * ============================================================ */

function extractContentFromPayload(payload: unknown): string {
  if (typeof payload === 'string') {
    return payload;
  }

  if (!isRecord(payload)) {
    return '';
  }

  if (typeof payload.content === 'string') {
    return payload.content;
  }

  if (typeof payload.text === 'string') {
    return payload.text;
  }

  if (typeof payload.token === 'string') {
    return payload.token;
  }

  if (isRecord(payload.token)) {
    if (typeof payload.token.content === 'string') {
      return payload.token.content;
    }

    if (typeof payload.token.text === 'string') {
      return payload.token.text;
    }
  }

  if (typeof payload.delta === 'string') {
    return payload.delta;
  }

  if (isRecord(payload.delta) && typeof payload.delta.content === 'string') {
    return payload.delta.content;
  }

  if (typeof payload.message === 'string') {
    return payload.message;
  }

  if (isRecord(payload.message) && typeof payload.message.content === 'string') {
    return payload.message.content;
  }

  return '';
}

function extractErrorMessage(payload: unknown, fallback: string): string {
  if (typeof payload === 'string') {
    return payload.trim() || fallback;
  }

  if (!isRecord(payload)) {
    return fallback;
  }

  if (typeof payload.message === 'string' && payload.message.trim()) {
    return payload.message;
  }

  if (typeof payload.detail === 'string' && payload.detail.trim()) {
    return payload.detail;
  }

  if (
    isRecord(payload.error) &&
    typeof payload.error.message === 'string' &&
    payload.error.message.trim()
  ) {
    return payload.error.message;
  }

  return fallback;
}

function formatRequestError(error: unknown): string {
  if (error instanceof ApiError) {
    const requestReference = error.requestId ? ` Request-ID: ${error.requestId}.` : '';

    return `${error.message}${requestReference}`;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return 'Die Nachricht konnte nicht gesendet werden.';
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

/* ============================================================
 * Komponente
 * ============================================================ */

export function GenericChatView({ title, hierarchyNodeId }: GenericChatViewProps) {
  const [input, setInput] = useState('');

  const [messages, setMessages] = useState<ChatMessage[]>([]);

  const [requestStatus, setRequestStatus] = useState<ChatRequestStatus>('idle');

  const [error, setError] = useState<string | null>(null);

  const [conversationId, setConversationId] = useState<string | null>(null);

  const abortControllerRef = useRef<AbortController | null>(null);

  const streamHandleRef = useRef<ApiStreamHandle | null>(null);

  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  const textareaRef = useRef<HTMLTextAreaElement | null>(null);

  const loading = requestStatus === 'connecting' || requestStatus === 'streaming';

  /* ----------------------------------------------------------
   * Lebenszyklus
   * ---------------------------------------------------------- */

  useEffect(() => {
    logDeveloperStep('info', 'chat-context-activated', {
      hierarchyNodeId,
      title,
    });

    setMessages([]);
    setConversationId(null);
    setInput('');
    setError(null);
    setRequestStatus('idle');

    return () => {
      logDeveloperStep('info', 'chat-context-deactivated', {
        hierarchyNodeId,
        hasAbortController: abortControllerRef.current !== null,
        hasStreamHandle: streamHandleRef.current !== null,
      });

      streamHandleRef.current?.cancel();
      streamHandleRef.current?.dispose();
      streamHandleRef.current = null;

      abortControllerRef.current?.abort();
      abortControllerRef.current = null;
    };
  }, [hierarchyNodeId, title]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({
      behavior: 'smooth',
      block: 'end',
    });
  }, [messages]);

  useEffect(() => {
    const textarea = textareaRef.current;

    if (!textarea) {
      return;
    }

    textarea.style.height = 'auto';

    textarea.style.height = `${Math.min(textarea.scrollHeight, MAX_INPUT_HEIGHT)}px`;
  }, [input]);

  /* ----------------------------------------------------------
   * Nachrichten-State
   * ---------------------------------------------------------- */

  function updateAssistantMessage(assistantMessageId: string, update: Partial<ChatMessage>): void {
    setMessages((currentMessages) =>
      currentMessages.map((message) =>
        message.id === assistantMessageId
          ? {
              ...message,
              ...update,
            }
          : message,
      ),
    );
  }

  function appendAssistantContent(
    assistantMessageId: string,
    content: string,
    metadata: {
      requestId?: string | null;
      conversationId?: string | null;
      messageId?: string | null;
    } = {},
  ): void {
    if (!content) {
      return;
    }

    setMessages((currentMessages) =>
      currentMessages.map((message) => {
        if (message.id !== assistantMessageId) {
          return message;
        }

        return {
          ...message,
          content: message.content + content,
          status: 'streaming',
          requestId: metadata.requestId ?? message.requestId,
          conversationId: metadata.conversationId ?? message.conversationId,
          serverMessageId: metadata.messageId ?? message.serverMessageId,
        };
      }),
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
    } = {},
  ): void {
    setMessages((currentMessages) =>
      currentMessages.map((message) => {
        if (message.id !== assistantMessageId) {
          return message;
        }

        return {
          ...message,
          content,
          status: metadata.status ?? 'streaming',
          requestId: metadata.requestId ?? message.requestId,
          conversationId: metadata.conversationId ?? message.conversationId,
          serverMessageId: metadata.messageId ?? message.serverMessageId,
        };
      }),
    );
  }

  /* ----------------------------------------------------------
   * Streamverarbeitung
   * ---------------------------------------------------------- */

  async function processSseStream(
    streamHandle: ApiStreamHandle,
    assistantMessageId: string,
    abortSignal: AbortSignal,
  ): Promise<void> {
    const response = streamHandle.response;

    if (!response.body) {
      throw new Error('Der Server hat keinen lesbaren Datenstrom geliefert.');
    }

    const headerRequestId = streamHandle.requestId ?? response.headers.get('x-request-id');

    const contentType = response.headers.get('content-type');

    logDeveloperStep('info', 'sse-stream-opened', {
      status: response.status,
      contentType,
      requestId: headerRequestId,
      clientRequestId: streamHandle.clientRequestId,
    });

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

      if (!rawEvent) {
        return;
      }

      const streamEvent = parseChatStreamEvent(rawEvent);

      if (streamEvent.schemaVersion !== CHAT_STREAM_SCHEMA_VERSION) {
        throw new Error(
          'Der Server verwendet eine nicht unterstützte Chat-Stream-Version. ' +
            `Erwartet: ${CHAT_STREAM_SCHEMA_VERSION}, ` +
            `erhalten: ${streamEvent.schemaVersion ?? 'nicht angegeben'}.`,
        );
      }

      if (streamEvent.sequence !== null) {
        if (lastSequence !== null && streamEvent.sequence < lastSequence) {
          throw new Error('Der Chat-Stream enthält eine ungültige Ereignisreihenfolge.');
        }

        if (lastSequence !== null && streamEvent.sequence === lastSequence) {
          logDeveloperStep('warn', 'duplicate-sse-event-ignored', {
            sequence: streamEvent.sequence,
            eventType: streamEvent.type,
          });

          return;
        }

        lastSequence = streamEvent.sequence;
      }

      processedEventCount += 1;

      logDeveloperStep('debug', 'sse-event-received', {
        eventType: streamEvent.type,
        sequence: streamEvent.sequence,
        requestId: streamEvent.requestId ?? headerRequestId,
        conversationId: streamEvent.conversationId,
        messageId: streamEvent.messageId,
        eventCount: processedEventCount,
      });

      if (!KNOWN_STREAM_EVENT_TYPES.has(streamEvent.type as ChatStreamEventType)) {
        logDeveloperStep('warn', 'unsupported-sse-event-ignored', {
          eventType: streamEvent.type,
          sequence: streamEvent.sequence,
        });

        return;
      }

      const eventType = streamEvent.type as ChatStreamEventType;

      const requestId = streamEvent.requestId ?? headerRequestId;

      switch (eventType) {
        case 'start': {
          setRequestStatus('streaming');

          if (streamEvent.conversationId) {
            setConversationId(streamEvent.conversationId);
          }

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

          if (!content) {
            return;
          }

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

          if (!content) {
            return;
          }

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

          if (streamEvent.conversationId) {
            setConversationId(streamEvent.conversationId);
          }

          logDeveloperStep('info', 'generation-completed', {
            requestId,
            conversationId: streamEvent.conversationId,
            messageId: streamEvent.messageId,
            receivedCharacterCount,
            processedEventCount,
          });

          break;
        }

        case 'error': {
          errorReceived = true;

          const message = extractErrorMessage(
            streamEvent.payload,
            'Beim Verarbeiten der Nachricht ist ein Fehler aufgetreten.',
          );

          logDeveloperStep('error', 'sse-error-event-received', {
            requestId,
            sequence: streamEvent.sequence,
            message,
          });

          throw new Error(message);
        }

        case 'heartbeat': {
          logDeveloperStep('debug', 'sse-heartbeat-received', {
            sequence: streamEvent.sequence,
          });

          break;
        }

        case 'reasoning':
        case 'tool_call':
        case 'tool_result':
        case 'usage': {
          logDeveloperStep('debug', 'sse-metadata-event-received', {
            eventType,
            sequence: streamEvent.sequence,
          });

          break;
        }
      }
    }

    try {
      while (true) {
        if (abortSignal.aborted) {
          throw new DOMException('Die Anfrage wurde abgebrochen.', 'AbortError');
        }

        const { value, done } = await reader.read();

        if (done) {
          buffer += decoder.decode();
          break;
        }

        buffer += decoder.decode(value, {
          stream: true,
        });

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
      } catch {
        // Der Reader kann bei einem Abbruch bereits freigegeben sein.
      }

      logDeveloperStep('info', 'sse-stream-closed', {
        completeReceived,
        errorReceived,
        processedEventCount,
        receivedCharacterCount,
        aborted: abortSignal.aborted,
      });
    }

    if (!completeReceived && !errorReceived && !abortSignal.aborted) {
      throw new Error(
        'Die Verbindung wurde beendet, bevor der Server den Chat-Stream ordnungsgemäß abgeschlossen hat.',
      );
    }
  }

  /* ----------------------------------------------------------
   * Absenden
   * ---------------------------------------------------------- */

  async function submit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();

    if (loading) {
      logDeveloperStep('warn', 'submit-ignored-request-active');
      return;
    }

    let prompt: string;

    try {
      prompt = validatePrompt(input);
    } catch (validationError) {
      const message =
        validationError instanceof Error ? validationError.message : 'Die Nachricht ist ungültig.';

      setError(message);

      logDeveloperStep('warn', 'input-validation-failed', {
        message,
        inputLength: input.length,
      });

      return;
    }

    const userMessageId = createMessageId();

    const assistantMessageId = createMessageId();

    const submittedAt = Date.now();

    const activeConversationId = conversationId;

    const userMessage: ChatMessage = {
      id: userMessageId,
      role: 'user',
      content: prompt,
      timestamp: submittedAt,
      status: 'completed',
      conversationId: activeConversationId ?? undefined,
    };

    const assistantMessage: ChatMessage = {
      id: assistantMessageId,
      role: 'assistant',
      content: '',
      timestamp: submittedAt,
      status: 'pending',
      conversationId: activeConversationId ?? undefined,
    };

    const requestPayload: ChatRequestPayload = {
      message: prompt,
      conversation_id: activeConversationId,
      hierarchy_node_id: hierarchyNodeId,
      model_id: null,
      tool_ids: [],
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
      const message =
        validationError instanceof Error
          ? validationError.message
          : 'Die Chat-Anfrage ist ungültig.';

      setError(message);

      logDeveloperStep('warn', 'chat-request-validation-failed', {
        message,
      });

      return;
    }

    logDeveloperStep('info', 'submit-started', {
      userMessageId,
      assistantMessageId,
      hierarchyNodeId,
      conversationId: activeConversationId,
      promptLength: prompt.length,
      toolCount: requestPayload.tool_ids.length,
      modelId: requestPayload.model_id,
    });

    setMessages((currentMessages) => [...currentMessages, userMessage, assistantMessage]);

    setInput('');
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

      await processSseStream(streamHandle, assistantMessageId, abortController.signal);

      setMessages((currentMessages) =>
        currentMessages.map((message) => {
          if (message.id !== assistantMessageId) {
            return message;
          }

          if (message.content.trim() === '') {
            return {
              ...message,
              content: 'Der Server hat keine Antwort geliefert.',
              status: 'completed',
            };
          }

          return {
            ...message,
            status: 'completed',
          };
        }),
      );

      setRequestStatus('completed');

      logDeveloperStep('info', 'submit-completed', {
        assistantMessageId,
        requestId: streamHandle.requestId,
        clientRequestId: streamHandle.clientRequestId,
      });
    } catch (caughtError) {
      const requestWasAborted =
        abortController.signal.aborted ||
        isAbortError(caughtError) ||
        (caughtError instanceof ApiError && caughtError.code === 'request_aborted');

      if (requestWasAborted) {
        setRequestStatus('cancelled');

        setAssistantContent(assistantMessageId, 'Die Antwort wurde abgebrochen.', {
          status: 'cancelled',
        });

        logDeveloperStep('info', 'generation-cancelled', {
          assistantMessageId,
          requestId: streamHandle?.requestId,
          clientRequestId: streamHandle?.clientRequestId,
        });

        return;
      }

      const message = formatRequestError(caughtError);

      setRequestStatus('failed');
      setError(message);

      setAssistantContent(assistantMessageId, `Fehler: ${message}`, {
        status: 'failed',
        requestId: caughtError instanceof ApiError ? caughtError.requestId : null,
      });

      logDeveloperStep('error', 'submit-failed', {
        assistantMessageId,
        errorName: caughtError instanceof Error ? caughtError.name : null,
        errorCode: caughtError instanceof ApiError ? caughtError.code : null,
        requestId: caughtError instanceof ApiError ? caughtError.requestId : null,
        clientRequestId: caughtError instanceof ApiError ? caughtError.clientRequestId : null,
        message,
      });
    } finally {
      streamHandle?.dispose();

      if (streamHandleRef.current === streamHandle) {
        streamHandleRef.current = null;
      }

      if (abortControllerRef.current === abortController) {
        abortControllerRef.current = null;
      }

      logDeveloperStep('debug', 'submit-cleanup-completed', {
        aborted: abortController.signal.aborted,
      });
    }
  }

  /* ----------------------------------------------------------
   * Bedienung
   * ---------------------------------------------------------- */

  function stopGeneration(): void {
    const streamHandle = streamHandleRef.current;

    const abortController = abortControllerRef.current;

    if (!streamHandle && !abortController) {
      logDeveloperStep('debug', 'stop-ignored-no-active-request');
      return;
    }

    logDeveloperStep('info', 'stop-requested-by-user', {
      requestStatus,
      hasStreamHandle: streamHandle !== null,
      hasAbortController: abortController !== null,
    });

    streamHandle?.cancel();

    abortController?.abort(
      new DOMException('Die Antwort wurde vom Benutzer abgebrochen.', 'AbortError'),
    );
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

  /* ----------------------------------------------------------
   * Darstellung
   * ---------------------------------------------------------- */

  const activeAssistantMessage = [...messages]
    .reverse()
    .find(
      (message) =>
        message.role === 'assistant' &&
        (message.status === 'pending' || message.status === 'streaming'),
    );

  const showTypingIndicator =
    loading && Boolean(activeAssistantMessage) && !activeAssistantMessage?.content;

  const accessibleStatus = getAccessibleRequestStatus(requestStatus);

  return (
    <section
      className="flex h-full min-h-0 min-w-0 w-full flex-1 flex-col overflow-hidden bg-surface-muted dark:bg-slate-900/30"
      aria-label={`Chat: ${title}`}
    >
      <p className="sr-only" aria-live="polite">
        {accessibleStatus}
      </p>

      {/* Nachrichtenbereich */}
      <div
        className="min-h-0 min-w-0 flex-1 overflow-y-auto overscroll-contain"
        aria-live="polite"
        aria-busy={loading}
      >
        <div className="flex min-h-full w-full flex-col px-4 py-6 sm:px-6 lg:px-8">
          {messages.length === 0 ? (
            <div className="flex min-h-0 flex-1 items-center justify-center py-10">
              <div className="w-full max-w-md text-center text-text-muted dark:text-gray-400">
                <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl border border-border-soft bg-white/70 shadow-sm dark:border-white/10 dark:bg-slate-800/60">
                  <MessageCircle size={27} className="opacity-60" aria-hidden="true" />
                </div>

                <p className="text-base font-medium text-text-soft dark:text-gray-300">
                  Noch keine Nachrichten
                </p>

                <p className="mt-1 text-sm">Schreibe eine Nachricht, um diesen Chat zu beginnen.</p>
              </div>
            </div>
          ) : (
            <div className="w-full space-y-5">
              {messages.map((message) => {
                const isUser = message.role === 'user';

                const isSystem = message.role === 'system';

                const isEmptyActiveAssistant =
                  !isUser &&
                  !message.content &&
                  (message.status === 'pending' || message.status === 'streaming');

                if (isSystem || isEmptyActiveAssistant) {
                  return null;
                }

                return (
                  <article
                    key={message.id}
                    className={[
                      'flex w-full',
                      'animate-fade-in',
                      'items-start gap-3',
                      isUser ? 'flex-row-reverse' : 'flex-row',
                    ].join(' ')}
                    data-message-id={message.id}
                    data-message-status={message.status}
                  >
                    <div
                      className={[
                        'flex h-9 w-9 shrink-0',
                        'items-center justify-center',
                        'rounded-full text-xs',
                        'font-bold uppercase ring-1',
                        isUser
                          ? [
                              'bg-primary-soft',
                              'text-primary',
                              'ring-primary/15',
                              'dark:bg-primary/20',
                              'dark:text-primary',
                              'dark:ring-primary/25',
                            ].join(' ')
                          : [
                              'bg-secondary-soft',
                              'text-secondary',
                              'ring-secondary/15',
                              'dark:bg-secondary/20',
                              'dark:text-secondary',
                              'dark:ring-secondary/25',
                            ].join(' '),
                      ].join(' ')}
                      aria-hidden="true"
                    >
                      {getInitials(message.role)}
                    </div>

                    <div
                      className={[
                        'min-w-0 rounded-2xl',
                        'px-4 py-3 shadow-sm',
                        isUser
                          ? [
                              'max-w-[min(85%,52rem)]',
                              'bg-linear-to-br',
                              'from-primary',
                              'to-primary-active',
                              'text-white',
                              'dark:from-primary-dark',
                              'dark:to-primary-active-dark',
                            ].join(' ')
                          : [
                              'w-full max-w-6xl',
                              'border',
                              'border-border-soft',
                              'bg-white/90',
                              'backdrop-blur-sm',
                              'dark:border-white/10',
                              'dark:bg-slate-800/80',
                            ].join(' '),
                      ].join(' ')}
                    >
                      <div className="flex items-center justify-between gap-4">
                        <span
                          className={[
                            'text-xs font-semibold',
                            isUser ? 'text-white/80' : 'text-text-muted dark:text-gray-400',
                          ].join(' ')}
                        >
                          {isUser ? 'Du' : 'Assistent'}
                        </span>

                        <time
                          dateTime={new Date(message.timestamp).toISOString()}
                          className={[
                            'shrink-0 text-xs',
                            isUser ? 'text-white/60' : 'text-text-subtle dark:text-gray-500',
                          ].join(' ')}
                        >
                          {formatTime(message.timestamp)}
                        </time>
                      </div>

                      <p
                        className={[
                          'mt-1 wrap-break-words',
                          'whitespace-pre-wrap',
                          'text-sm leading-6',
                          isUser ? 'text-white' : 'text-text dark:text-gray-100',
                        ].join(' ')}
                      >
                        {message.content}
                      </p>
                    </div>
                  </article>
                );
              })}

              {showTypingIndicator ? (
                <div className="flex w-full animate-fade-in items-start gap-3">
                  <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-secondary-soft text-xs font-bold uppercase text-secondary ring-1 ring-secondary/15 dark:bg-secondary/20 dark:text-secondary dark:ring-secondary/25">
                    KI
                  </div>

                  <div className="rounded-2xl border border-border-soft bg-white/90 px-4 py-3 shadow-sm backdrop-blur-sm dark:border-white/10 dark:bg-slate-800/80">
                    <div className="flex items-center gap-1">
                      <span className="h-2 w-2 animate-pulse rounded-full bg-primary/60" />

                      <span className="animation-delay-200 h-2 w-2 animate-pulse rounded-full bg-primary/60" />

                      <span className="animation-delay-400 h-2 w-2 animate-pulse rounded-full bg-primary/60" />

                      <span className="ml-2 text-sm text-text-muted dark:text-gray-400">
                        Antwort wird erstellt …
                      </span>
                    </div>
                  </div>
                </div>
              ) : null}

              <div ref={messagesEndRef} aria-hidden="true" />
            </div>
          )}
        </div>
      </div>

      {/* Fehleranzeige */}
      {error ? (
        <div
          className="shrink-0 border-t border-danger/20 bg-danger-soft px-4 py-2.5 text-sm text-danger dark:bg-danger/10 sm:px-6 lg:px-8"
          role="alert"
        >
          <div className="w-full">
            <span className="font-medium">Fehler:</span> {error}
          </div>
        </div>
      ) : null}

      {/* Eingabebereich */}
      <form
        onSubmit={submit}
        className="shrink-0 border-t border-border bg-white/85 px-4 py-3 backdrop-blur-md dark:border-white/10 dark:bg-slate-900/75 sm:px-6 lg:px-8"
      >
        <div className="w-full">
          <div className="flex w-full min-w-0 items-end gap-2">
            <label htmlFor="chat-message-input" className="sr-only">
              Nachricht
            </label>

            <textarea
              ref={textareaRef}
              id="chat-message-input"
              rows={1}
              className="max-h-48 min-h-11 min-w-0 flex-1 resize-none overflow-y-auto rounded-xl border border-border-soft bg-surface-muted px-4 py-2.5 text-sm leading-6 text-text outline-none transition placeholder:text-text-subtle focus:border-primary focus:ring-4 focus:ring-primary-soft disabled:cursor-not-allowed disabled:opacity-60 dark:border-white/10 dark:bg-slate-800/50 dark:text-white dark:placeholder:text-gray-500 dark:focus:ring-primary/20"
              value={input}
              onChange={(event) => {
                setInput(event.target.value);
              }}
              onKeyDown={handleInputKeyDown}
              placeholder="Nachricht eingeben …"
              autoComplete="off"
              disabled={loading}
              maxLength={MAX_MESSAGE_LENGTH}
            />

            {loading ? (
              <button
                type="button"
                className="inline-flex h-11 w-11 shrink-0 items-center justify-center rounded-xl border border-border-soft bg-surface text-text-soft shadow-sm transition hover:bg-surface-hover hover:text-text focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 dark:border-white/10 dark:bg-slate-800/70 dark:text-gray-300 dark:hover:bg-slate-700/70 dark:hover:text-white dark:focus-visible:ring-offset-slate-900"
                onClick={stopGeneration}
                aria-label="Antwort abbrechen"
                title="Antwort abbrechen"
              >
                <Square size={18} aria-hidden="true" />
              </button>
            ) : (
              <button
                type="submit"
                className="inline-flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-primary text-white shadow-glow transition hover:bg-primary-hover hover:shadow-primary-glow focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-40 dark:bg-primary-dark dark:hover:bg-primary-dark-hover dark:focus-visible:ring-offset-slate-900"
                disabled={!input.trim()}
                aria-label="Nachricht senden"
                title="Nachricht senden"
              >
                <Send size={18} aria-hidden="true" />
              </button>
            )}
          </div>

          <div className="mt-2 flex items-center justify-between gap-4 text-xs text-text-muted dark:text-gray-500">
            <p className="truncate">
              Enter sendet · Shift + Enter erzeugt eine neue Zeile · Escape bricht ab
            </p>

            <span className="shrink-0 tabular-nums">
              {input.length.toLocaleString('de-DE')}/{MAX_MESSAGE_LENGTH.toLocaleString('de-DE')}
            </span>
          </div>
        </div>
      </form>
    </section>
  );
}
