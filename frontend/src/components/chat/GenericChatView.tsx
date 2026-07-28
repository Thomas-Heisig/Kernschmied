// F:\Kernschmied\frontend\src\components\chat\GenericChatView.tsx

/// <reference types="react" />

import React, {
  FormEvent,
  KeyboardEvent,
  useEffect,
  useRef,
  useState,
} from "react";

import { API_BASE_URL } from "../../api/client";

const SOURCE_FILE =
  "frontend/src/components/chat/GenericChatView.tsx";

const CHAT_STREAM_PATH = "/chat/stream";
const CHAT_SCHEMA_VERSION = "1.0";
const MAX_MESSAGE_LENGTH = 50_000;

type GenericChatViewProps = {
  title: string;
  hierarchyNodeId: string;
};

type ChatRole =
  | "user"
  | "assistant"
  | "system";

type ChatRequestStatus =
  | "idle"
  | "connecting"
  | "streaming"
  | "completed"
  | "failed"
  | "cancelled";

type ChatMessageStatus =
  | "pending"
  | "streaming"
  | "completed"
  | "failed"
  | "cancelled";

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
  schema_version: string;
  message: string;
  conversation_id: string | null;
  hierarchy_node_id: string;
  model_id: string | null;
  tool_ids: string[];
  metadata: Record<string, unknown>;
};

type RawSseEvent = {
  event: string;
  id: string | null;
  data: string;
};

type ChatStreamEventType =
  | "start"
  | "token"
  | "message"
  | "reasoning"
  | "tool_call"
  | "tool_result"
  | "usage"
  | "complete"
  | "done"
  | "error"
  | "heartbeat";

type ChatStreamEnvelope = {
  schema_version?: unknown;
  event?: unknown;
  sequence?: unknown;
  request_id?: unknown;
  conversation_id?: unknown;
  message_id?: unknown;
  data?: unknown;
  content?: unknown;
  message?: unknown;
  detail?: unknown;
  code?: unknown;
};

type ParsedChatStreamEvent = {
  type: string;
  sequence: number | null;
  requestId: string | null;
  conversationId: string | null;
  messageId: string | null;
  payload: unknown;
  rawData: string;
};

type ApiErrorBody = {
  code?: unknown;
  message?: unknown;
  detail?: unknown;
  details?: unknown;
  request_id?: unknown;
};

type DeveloperLogLevel =
  | "debug"
  | "info"
  | "warn"
  | "error";

type DeveloperLogContext = Record<
  string,
  unknown
>;

const KNOWN_STREAM_EVENT_TYPES =
  new Set<ChatStreamEventType>([
    "start",
    "token",
    "message",
    "reasoning",
    "tool_call",
    "tool_result",
    "usage",
    "complete",
    "done",
    "error",
    "heartbeat",
  ]);

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
    area: "chat-pipeline",
    step,
    ...context,
  };

  switch (level) {
    case "error":
      console.error(
        "[Kernschmied][ChatPipeline]",
        entry,
      );
      break;

    case "warn":
      console.warn(
        "[Kernschmied][ChatPipeline]",
        entry,
      );
      break;

    case "info":
      console.info(
        "[Kernschmied][ChatPipeline]",
        entry,
      );
      break;

    default:
      console.debug(
        "[Kernschmied][ChatPipeline]",
        entry,
      );
  }
}

function createMessageId(): string {
  if (
    typeof crypto !== "undefined" &&
    typeof crypto.randomUUID === "function"
  ) {
    return crypto.randomUUID();
  }

  return [
    "message",
    Date.now().toString(36),
    Math.random().toString(36).slice(2),
  ].join("-");
}

function normalizeSseBuffer(
  value: string,
): string {
  return value
    .replace(/\r\n/g, "\n")
    .replace(/\r/g, "\n");
}

function parseSseEvent(
  chunk: string,
): RawSseEvent | null {
  let event = "message";
  let id: string | null = null;

  const dataLines: string[] = [];

  for (const line of chunk.split("\n")) {
    if (!line || line.startsWith(":")) {
      continue;
    }

    const separatorIndex = line.indexOf(":");

    let field: string;
    let fieldValue: string;

    if (separatorIndex === -1) {
      field = line;
      fieldValue = "";
    } else {
      field = line.slice(
        0,
        separatorIndex,
      );

      fieldValue = line.slice(
        separatorIndex + 1,
      );

      if (fieldValue.startsWith(" ")) {
        fieldValue = fieldValue.slice(1);
      }
    }

    switch (field) {
      case "event":
        event = fieldValue;
        break;

      case "id":
        id = fieldValue || null;
        break;

      case "data":
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
    data: dataLines.join("\n"),
  };
}

function isRecord(
  value: unknown,
): value is Record<string, unknown> {
  return (
    typeof value === "object" &&
    value !== null &&
    !Array.isArray(value)
  );
}

function asOptionalString(
  value: unknown,
): string | null {
  return typeof value === "string"
    ? value
    : null;
}

function asOptionalNumber(
  value: unknown,
): number | null {
  if (
    typeof value === "number" &&
    Number.isFinite(value)
  ) {
    return value;
  }

  if (
    typeof value === "string" &&
    value.trim() !== ""
  ) {
    const parsed = Number(value);

    return Number.isFinite(parsed)
      ? parsed
      : null;
  }

  return null;
}

function parseChatStreamEvent(
  rawEvent: RawSseEvent,
): ParsedChatStreamEvent {
  if (
    rawEvent.data === "[DONE]"
  ) {
    return {
      type: "complete",
      sequence: asOptionalNumber(
        rawEvent.id,
      ),
      requestId: null,
      conversationId: null,
      messageId: null,
      payload: null,
      rawData: rawEvent.data,
    };
  }

  try {
    const parsed = JSON.parse(
      rawEvent.data,
    ) as unknown;

    if (!isRecord(parsed)) {
      return {
        type: rawEvent.event,
        sequence: asOptionalNumber(
          rawEvent.id,
        ),
        requestId: null,
        conversationId: null,
        messageId: null,
        payload: parsed,
        rawData: rawEvent.data,
      };
    }

    const envelope =
      parsed as ChatStreamEnvelope;

    return {
      type:
        typeof envelope.event === "string"
          ? envelope.event
          : rawEvent.event,
      sequence:
        asOptionalNumber(
          envelope.sequence,
        ) ??
        asOptionalNumber(
          rawEvent.id,
        ),
      requestId: asOptionalString(
        envelope.request_id,
      ),
      conversationId: asOptionalString(
        envelope.conversation_id,
      ),
      messageId: asOptionalString(
        envelope.message_id,
      ),
      payload:
        envelope.data !== undefined
          ? envelope.data
          : parsed,
      rawData: rawEvent.data,
    };
  } catch {
    return {
      type: rawEvent.event,
      sequence: asOptionalNumber(
        rawEvent.id,
      ),
      requestId: null,
      conversationId: null,
      messageId: null,
      payload: rawEvent.data,
      rawData: rawEvent.data,
    };
  }
}

function extractContentFromPayload(
  payload: unknown,
): string {
  if (typeof payload === "string") {
    return payload;
  }

  if (!isRecord(payload)) {
    return "";
  }

  const directContent =
    payload.content;

  if (
    typeof directContent === "string"
  ) {
    return directContent;
  }

  const token = payload.token;

  if (typeof token === "string") {
    return token;
  }

  if (isRecord(token)) {
    const tokenContent = token.content;

    if (
      typeof tokenContent === "string"
    ) {
      return tokenContent;
    }

    const tokenText = token.text;

    if (
      typeof tokenText === "string"
    ) {
      return tokenText;
    }
  }

  const delta = payload.delta;

  if (typeof delta === "string") {
    return delta;
  }

  if (isRecord(delta)) {
    const deltaContent = delta.content;

    if (
      typeof deltaContent === "string"
    ) {
      return deltaContent;
    }
  }

  const message = payload.message;

  if (typeof message === "string") {
    return message;
  }

  if (isRecord(message)) {
    const messageContent =
      message.content;

    if (
      typeof messageContent === "string"
    ) {
      return messageContent;
    }
  }

  return "";
}

function extractErrorMessage(
  payload: unknown,
  fallback: string,
): string {
  if (typeof payload === "string") {
    const normalized = payload.trim();

    return normalized || fallback;
  }

  if (!isRecord(payload)) {
    return fallback;
  }

  if (
    typeof payload.message === "string"
  ) {
    return payload.message;
  }

  if (
    typeof payload.detail === "string"
  ) {
    return payload.detail;
  }

  if (isRecord(payload.error)) {
    const nestedMessage =
      payload.error.message;

    if (
      typeof nestedMessage === "string"
    ) {
      return nestedMessage;
    }
  }

  return fallback;
}

function formatValidationDetails(
  detail: unknown,
): string | null {
  if (!Array.isArray(detail)) {
    return null;
  }

  const messages = detail.map(
    (entry) => {
      if (!isRecord(entry)) {
        return String(entry);
      }

      const location =
        Array.isArray(entry.loc)
          ? entry.loc.join(".")
          : "request";

      const message =
        typeof entry.msg === "string"
          ? entry.msg
          : "Ungültiger Wert";

      return `${location}: ${message}`;
    },
  );

  return messages.join("; ");
}

async function readApiErrorMessage(
  response: Response,
): Promise<string> {
  const fallback =
    `Die Anfrage ist fehlgeschlagen (${response.status}).`;

  const responseClone = response.clone();

  try {
    const body =
      (await response.json()) as ApiErrorBody;

    logDeveloperStep(
      "error",
      "http-error-response-parsed",
      {
        status: response.status,
        statusText: response.statusText,
        code:
          typeof body.code === "string"
            ? body.code
            : null,
        requestId:
          typeof body.request_id === "string"
            ? body.request_id
            : null,
        detailsAvailable:
          body.details !== undefined,
      },
    );

    if (
      typeof body.message === "string"
    ) {
      return body.message;
    }

    if (
      typeof body.detail === "string"
    ) {
      return body.detail;
    }

    const validationDetails =
      formatValidationDetails(
        body.detail,
      );

    if (validationDetails) {
      return validationDetails;
    }

    if (body.details !== undefined) {
      try {
        return JSON.stringify(
          body.details,
          null,
          2,
        );
      } catch {
        return fallback;
      }
    }
  } catch (parseError) {
    logDeveloperStep(
      "warn",
      "http-error-json-parse-failed",
      {
        status: response.status,
        error:
          parseError instanceof Error
            ? parseError.message
            : String(parseError),
      },
    );
  }

  try {
    const responseText =
      await responseClone.text();

    if (responseText.trim()) {
      return responseText.trim();
    }
  } catch (readError) {
    logDeveloperStep(
      "warn",
      "http-error-text-read-failed",
      {
        status: response.status,
        error:
          readError instanceof Error
            ? readError.message
            : String(readError),
      },
    );
  }

  return fallback;
}

function isAbortError(
  error: unknown,
): boolean {
  return (
    error instanceof DOMException &&
    error.name === "AbortError"
  );
}

function validatePrompt(
  value: string,
): string {
  const normalized = value.trim();

  if (!normalized) {
    throw new Error(
      "Die Nachricht darf nicht leer sein.",
    );
  }

  if (
    normalized.length >
    MAX_MESSAGE_LENGTH
  ) {
    throw new Error(
      `Die Nachricht darf höchstens ${MAX_MESSAGE_LENGTH.toLocaleString(
        "de-DE",
      )} Zeichen enthalten.`,
    );
  }

  return normalized;
}

export function GenericChatView({
  title,
  hierarchyNodeId,
}: GenericChatViewProps): React.JSX.Element {
  const [input, setInput] =
    useState("");

  const [messages, setMessages] =
    useState<ChatMessage[]>([]);

  const [requestStatus, setRequestStatus] =
    useState<ChatRequestStatus>("idle");

  const [error, setError] =
    useState<string | null>(null);

  const [conversationId, setConversationId] =
    useState<string | null>(null);

  const abortControllerRef =
    useRef<AbortController | null>(null);

  const messagesEndRef =
    useRef<HTMLDivElement | null>(null);

  const loading =
    requestStatus === "connecting" ||
    requestStatus === "streaming";

  useEffect(() => {
    logDeveloperStep(
      "info",
      "component-mounted",
      {
        hierarchyNodeId,
        title,
      },
    );

    return () => {
      logDeveloperStep(
        "info",
        "component-unmounting",
        {
          activeRequest:
            abortControllerRef.current !==
            null,
        },
      );

      abortControllerRef.current?.abort();
    };
  }, [
    hierarchyNodeId,
    title,
  ]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({
      behavior: "smooth",
      block: "end",
    });
  }, [messages]);

  function updateAssistantMessage(
    assistantMessageId: string,
    update: Partial<ChatMessage>,
  ): void {
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
        if (
          message.id !==
          assistantMessageId
        ) {
          return message;
        }

        return {
          ...message,
          content:
            message.content +
            content,
          status: "streaming",
          requestId:
            metadata.requestId ??
            message.requestId,
          conversationId:
            metadata.conversationId ??
            message.conversationId,
          serverMessageId:
            metadata.messageId ??
            message.serverMessageId,
        };
      }),
    );
  }

  function replaceAssistantContent(
    assistantMessageId: string,
    content: string,
    status: ChatMessageStatus,
  ): void {
    updateAssistantMessage(
      assistantMessageId,
      {
        content,
        status,
      },
    );
  }

  async function processSseStream(
    response: Response,
    assistantMessageId: string,
    abortSignal: AbortSignal,
  ): Promise<void> {
    if (!response.body) {
      throw new Error(
        "Der Server hat keinen lesbaren Datenstrom geliefert.",
      );
    }

    const contentType =
      response.headers.get(
        "content-type",
      );

    if (
      contentType &&
      !contentType
        .toLowerCase()
        .includes(
          "text/event-stream",
        )
    ) {
      logDeveloperStep(
        "warn",
        "unexpected-response-content-type",
        {
          contentType,
        },
      );
    }

    const headerRequestId =
      response.headers.get(
        "x-request-id",
      );

    logDeveloperStep(
      "info",
      "sse-stream-opened",
      {
        status: response.status,
        contentType,
        requestId: headerRequestId,
      },
    );

    const reader =
      response.body.getReader();

    const decoder =
      new TextDecoder("utf-8");

    let buffer = "";
    let completeReceived = false;
    let errorReceived = false;
    let processedEventCount = 0;
    let receivedCharacterCount = 0;
    let lastSequence: number | null =
      null;

    async function processChunk(
      chunk: string,
    ): Promise<void> {
      const rawEvent =
        parseSseEvent(chunk);

      if (!rawEvent) {
        logDeveloperStep(
          "debug",
          "sse-empty-event-ignored",
          {
            chunkLength: chunk.length,
          },
        );

        return;
      }

      const streamEvent =
        parseChatStreamEvent(
          rawEvent,
        );

      processedEventCount += 1;

      if (
        streamEvent.sequence !==
        null
      ) {
        if (
          lastSequence !== null &&
          streamEvent.sequence <=
            lastSequence
        ) {
          logDeveloperStep(
            "warn",
            "sse-sequence-not-increasing",
            {
              previousSequence:
                lastSequence,
              currentSequence:
                streamEvent.sequence,
              eventType:
                streamEvent.type,
            },
          );
        }

        lastSequence =
          streamEvent.sequence;
      }

      logDeveloperStep(
        "debug",
        "sse-event-received",
        {
          eventType:
            streamEvent.type,
          sequence:
            streamEvent.sequence,
          requestId:
            streamEvent.requestId ??
            headerRequestId,
          conversationId:
            streamEvent.conversationId,
          messageId:
            streamEvent.messageId,
          dataLength:
            rawEvent.data.length,
          eventCount:
            processedEventCount,
        },
      );

      if (
        !KNOWN_STREAM_EVENT_TYPES.has(
          streamEvent.type as ChatStreamEventType,
        )
      ) {
        logDeveloperStep(
          "warn",
          "sse-unsupported-event",
          {
            eventType:
              streamEvent.type,
            sequence:
              streamEvent.sequence,
          },
        );

        return;
      }

      switch (
        streamEvent.type as ChatStreamEventType
      ) {
        case "start": {
          setRequestStatus(
            "streaming",
          );

          if (
            streamEvent.conversationId
          ) {
            setConversationId(
              streamEvent.conversationId,
            );
          }

          updateAssistantMessage(
            assistantMessageId,
            {
              status: "streaming",
              requestId:
                streamEvent.requestId ??
                headerRequestId ??
                undefined,
              conversationId:
                streamEvent.conversationId ??
                undefined,
              serverMessageId:
                streamEvent.messageId ??
                undefined,
            },
          );

          logDeveloperStep(
            "info",
            "generation-started",
            {
              requestId:
                streamEvent.requestId ??
                headerRequestId,
              conversationId:
                streamEvent.conversationId,
              messageId:
                streamEvent.messageId,
            },
          );

          break;
        }

        case "token":
        case "message": {
          const content =
            extractContentFromPayload(
              streamEvent.payload,
            );

          if (!content) {
            logDeveloperStep(
              "debug",
              "sse-content-event-without-text",
              {
                eventType:
                  streamEvent.type,
                sequence:
                  streamEvent.sequence,
              },
            );

            break;
          }

          receivedCharacterCount +=
            content.length;

          appendAssistantContent(
            assistantMessageId,
            content,
            {
              requestId:
                streamEvent.requestId ??
                headerRequestId,
              conversationId:
                streamEvent.conversationId,
              messageId:
                streamEvent.messageId,
            },
          );

          break;
        }

        case "complete":
        case "done": {
          completeReceived = true;

          updateAssistantMessage(
            assistantMessageId,
            {
              status: "completed",
              requestId:
                streamEvent.requestId ??
                headerRequestId ??
                undefined,
              conversationId:
                streamEvent.conversationId ??
                undefined,
              serverMessageId:
                streamEvent.messageId ??
                undefined,
            },
          );

          if (
            streamEvent.conversationId
          ) {
            setConversationId(
              streamEvent.conversationId,
            );
          }

          logDeveloperStep(
            "info",
            "generation-completed",
            {
              requestId:
                streamEvent.requestId ??
                headerRequestId,
              conversationId:
                streamEvent.conversationId,
              messageId:
                streamEvent.messageId,
              receivedCharacterCount,
              processedEventCount,
            },
          );

          break;
        }

        case "error": {
          errorReceived = true;

          const message =
            extractErrorMessage(
              streamEvent.payload,
              "Beim Verarbeiten der Nachricht ist ein Fehler aufgetreten.",
            );

          logDeveloperStep(
            "error",
            "sse-error-event-received",
            {
              requestId:
                streamEvent.requestId ??
                headerRequestId,
              sequence:
                streamEvent.sequence,
              message,
            },
          );

          throw new Error(message);
        }

        case "heartbeat": {
          logDeveloperStep(
            "debug",
            "sse-heartbeat-received",
            {
              sequence:
                streamEvent.sequence,
            },
          );

          break;
        }

        case "reasoning":
        case "tool_call":
        case "tool_result":
        case "usage": {
          logDeveloperStep(
            "debug",
            "sse-metadata-event-received",
            {
              eventType:
                streamEvent.type,
              sequence:
                streamEvent.sequence,
            },
          );

          break;
        }
      }
    }

    try {
      while (true) {
        if (abortSignal.aborted) {
          throw new DOMException(
            "Die Anfrage wurde abgebrochen.",
            "AbortError",
          );
        }

        const {
          value,
          done,
        } = await reader.read();

        if (done) {
          buffer += decoder.decode();
          break;
        }

        buffer += decoder.decode(
          value,
          {
            stream: true,
          },
        );

        buffer =
          normalizeSseBuffer(
            buffer,
          );

        const chunks =
          buffer.split("\n\n");

        buffer =
          chunks.pop() ?? "";

        for (const chunk of chunks) {
          await processChunk(chunk);
        }
      }

      const remainingChunk =
        normalizeSseBuffer(
          buffer,
        ).trim();

      if (remainingChunk) {
        await processChunk(
          remainingChunk,
        );
      }
    } finally {
      try {
        reader.releaseLock();
      } catch {
        // Der Reader kann beim Abbruch bereits
        // freigegeben worden sein.
      }

      logDeveloperStep(
        "info",
        "sse-stream-closed",
        {
          completeReceived,
          errorReceived,
          processedEventCount,
          receivedCharacterCount,
          aborted:
            abortSignal.aborted,
        },
      );
    }

    if (
      !completeReceived &&
      !errorReceived &&
      !abortSignal.aborted
    ) {
      throw new Error(
        "Die Verbindung wurde beendet, bevor der Server den Chat-Stream ordnungsgemäß abgeschlossen hat.",
      );
    }
  }

  async function submit(
    event: FormEvent<HTMLFormElement>,
  ): Promise<void> {
    event.preventDefault();

    if (loading) {
      logDeveloperStep(
        "warn",
        "submit-ignored-request-active",
      );

      return;
    }

    let prompt: string;

    try {
      prompt = validatePrompt(input);
    } catch (validationError) {
      const message =
        validationError instanceof Error
          ? validationError.message
          : "Die Nachricht ist ungültig.";

      setError(message);

      logDeveloperStep(
        "warn",
        "input-validation-failed",
        {
          message,
          inputLength:
            input.length,
        },
      );

      return;
    }

    const userMessageId =
      createMessageId();

    const assistantMessageId =
      createMessageId();

    const now = Date.now();

    const userMessage: ChatMessage = {
      id: userMessageId,
      role: "user",
      content: prompt,
      timestamp: now,
      status: "completed",
      conversationId:
        conversationId ?? undefined,
    };

    const assistantMessage: ChatMessage = {
      id: assistantMessageId,
      role: "assistant",
      content: "",
      timestamp: now,
      status: "pending",
      conversationId:
        conversationId ?? undefined,
    };

    const requestPayload: ChatRequestPayload =
      {
        schema_version:
          CHAT_SCHEMA_VERSION,
        message: prompt,
        conversation_id:
          conversationId,
        hierarchy_node_id:
          hierarchyNodeId,
        model_id: null,
        tool_ids: [],
        metadata: {
          client: "kernschmied-web",
          client_message_id:
            userMessageId,
          client_assistant_message_id:
            assistantMessageId,
          submitted_at:
            new Date(
              now,
            ).toISOString(),
        },
      };

    logDeveloperStep(
      "info",
      "submit-started",
      {
        userMessageId,
        assistantMessageId,
        hierarchyNodeId,
        conversationId,
        promptLength:
          prompt.length,
        toolCount:
          requestPayload.tool_ids.length,
        modelId:
          requestPayload.model_id,
      },
    );

    setMessages(
      (currentMessages) => [
        ...currentMessages,
        userMessage,
        assistantMessage,
      ],
    );

    setInput("");
    setError(null);
    setRequestStatus(
      "connecting",
    );

    const abortController =
      new AbortController();

    abortControllerRef.current =
      abortController;

    try {
      const endpoint =
        `${API_BASE_URL}${CHAT_STREAM_PATH}`;

      logDeveloperStep(
        "info",
        "http-request-started",
        {
          endpoint,
          method: "POST",
          hierarchyNodeId,
          conversationId,
        },
      );

      const response =
        await fetch(endpoint, {
          method: "POST",
          headers: {
            Accept:
              "text/event-stream",
            "Content-Type":
              "application/json",
          },
          body: JSON.stringify(
            requestPayload,
          ),
          signal:
            abortController.signal,
        });

      logDeveloperStep(
        response.ok
          ? "info"
          : "warn",
        "http-response-received",
        {
          status:
            response.status,
          statusText:
            response.statusText,
          ok: response.ok,
          contentType:
            response.headers.get(
              "content-type",
            ),
          requestId:
            response.headers.get(
              "x-request-id",
            ),
        },
      );

      if (!response.ok) {
        const message =
          await readApiErrorMessage(
            response,
          );

        throw new Error(message);
      }

      setRequestStatus(
        "streaming",
      );

      await processSseStream(
        response,
        assistantMessageId,
        abortController.signal,
      );

      setMessages(
        (currentMessages) =>
          currentMessages.map(
            (message) => {
              if (
                message.id !==
                assistantMessageId
              ) {
                return message;
              }

              if (
                message.content.trim() ===
                ""
              ) {
                return {
                  ...message,
                  content:
                    "Der Server hat keine Antwort geliefert.",
                  status:
                    "completed",
                };
              }

              return {
                ...message,
                status:
                  "completed",
              };
            },
          ),
      );

      setRequestStatus(
        "completed",
      );

      logDeveloperStep(
        "info",
        "submit-completed",
        {
          assistantMessageId,
          conversationId,
        },
      );
    } catch (caughtError) {
      if (
        isAbortError(
          caughtError,
        ) ||
        abortController.signal.aborted
      ) {
        setRequestStatus(
          "cancelled",
        );

        replaceAssistantContent(
          assistantMessageId,
          "Die Antwort wurde abgebrochen.",
          "cancelled",
        );

        logDeveloperStep(
          "info",
          "generation-cancelled",
          {
            assistantMessageId,
          },
        );

        return;
      }

      const message =
        caughtError instanceof Error
          ? caughtError.message
          : "Die Nachricht konnte nicht gesendet werden.";

      setRequestStatus(
        "failed",
      );

      setError(message);

      replaceAssistantContent(
        assistantMessageId,
        `Fehler: ${message}`,
        "failed",
      );

      logDeveloperStep(
        "error",
        "submit-failed",
        {
          assistantMessageId,
          errorName:
            caughtError instanceof Error
              ? caughtError.name
              : null,
          message,
        },
      );
    } finally {
      if (
        abortControllerRef.current ===
        abortController
      ) {
        abortControllerRef.current =
          null;
      }

      logDeveloperStep(
        "debug",
        "submit-cleanup-completed",
        {
          finalStatus:
            abortController.signal.aborted
              ? "cancelled"
              : "finished",
        },
      );
    }
  }

  function stopGeneration(): void {
    if (
      !abortControllerRef.current
    ) {
      logDeveloperStep(
        "debug",
        "stop-ignored-no-active-request",
      );

      return;
    }

    logDeveloperStep(
      "info",
      "stop-requested-by-user",
      {
        requestStatus,
      },
    );

    abortControllerRef.current.abort();
  }

  function handleInputKeyDown(
    event: KeyboardEvent<HTMLInputElement>,
  ): void {
    if (
      event.key === "Escape" &&
      loading
    ) {
      event.preventDefault();
      stopGeneration();
    }
  }

  function getInitials(
    role: ChatRole,
  ): string {
    switch (role) {
      case "user":
        return "DU";

      case "assistant":
        return "AI";

      default:
        return "SY";
    }
  }

  function formatTime(
    timestamp: number,
  ): string {
    return new Date(
      timestamp,
    ).toLocaleTimeString(
      [],
      {
        hour: "2-digit",
        minute: "2-digit",
      },
    );
  }

  const activeAssistantMessage =
    [...messages]
      .reverse()
      .find(
        (message) =>
          message.role ===
            "assistant" &&
          (
            message.status ===
              "pending" ||
            message.status ===
              "streaming"
          ),
      );

  const showTypingIndicator =
    loading &&
    Boolean(
      activeAssistantMessage,
    ) &&
    !activeAssistantMessage
      ?.content;

  return (
    <section
      className="flex h-full min-h-0 flex-col bg-surface-muted dark:bg-slate-900/30"
      aria-label={`Chat: ${title}`}
    >
      <header className="shrink-0 border-b border-border bg-white/80 px-5 py-3 backdrop-blur-sm dark:border-white/10 dark:bg-slate-900/60">
        <h1 className="text-lg font-semibold text-text dark:text-white">
          {title}
        </h1>

        {import.meta.env.DEV ? (
          <div className="mt-1 flex flex-wrap gap-x-3 gap-y-1 text-[10px] text-text-subtle dark:text-gray-500">
            <span>
              Status: {requestStatus}
            </span>

            <span>
              Knoten: {hierarchyNodeId}
            </span>

            {conversationId ? (
              <span>
                Chat: {conversationId}
              </span>
            ) : null}
          </div>
        ) : null}
      </header>

      <div
        className="min-h-0 flex-1 space-y-4 overflow-y-auto p-5"
        aria-live="polite"
        aria-busy={loading}
      >
        {messages.length === 0 ? (
          <div className="flex h-full items-center justify-center">
            <div className="text-center text-text-muted dark:text-gray-400">
              <svg
                className="mx-auto mb-3 h-12 w-12 opacity-40"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                xmlns="http://www.w3.org/2000/svg"
                aria-hidden="true"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1.5}
                  d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
                />
              </svg>

              <p className="text-sm">
                Noch keine Nachrichten.
              </p>

              <p className="mt-1 text-xs">
                Stelle deine erste Frage.
              </p>
            </div>
          </div>
        ) : (
          messages.map(
            (message) => {
              const isUser =
                message.role === "user";

              const isSystem =
                message.role === "system";

              if (isSystem) {
                return null;
              }

              return (
                <article
                  key={message.id}
                  className={`flex animate-fade-in items-start gap-3 ${
                    isUser
                      ? "flex-row-reverse"
                      : "flex-row"
                  }`}
                  data-message-id={
                    message.id
                  }
                  data-message-status={
                    message.status
                  }
                >
                  <div
                    className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-xs font-bold uppercase ${
                      isUser
                        ? "bg-primary-soft text-primary dark:bg-primary/20 dark:text-primary"
                        : "bg-secondary-soft text-secondary dark:bg-secondary/20 dark:text-secondary"
                    }`}
                    aria-hidden="true"
                  >
                    {getInitials(
                      message.role,
                    )}
                  </div>

                  <div
                    className={`max-w-[85%] rounded-2xl px-4 py-3 shadow-sm ${
                      isUser
                        ? "bg-linear-to-br from-primary to-primary-active text-white dark:bg-primary-dark dark:to-primary-active-dark"
                        : "border border-border-soft bg-white/90 backdrop-blur-sm dark:border-white/10 dark:bg-slate-800/80"
                    }`}
                  >
                    <div className="flex items-center justify-between gap-4">
                      <span
                        className={`text-xs font-semibold ${
                          isUser
                            ? "text-white/80"
                            : "text-text-muted dark:text-gray-400"
                        }`}
                      >
                        {isUser
                          ? "Du"
                          : "Assistent"}
                      </span>

                      <time
                        dateTime={new Date(
                          message.timestamp,
                        ).toISOString()}
                        className={`text-xs ${
                          isUser
                            ? "text-white/60"
                            : "text-text-subtle dark:text-gray-500"
                        }`}
                      >
                        {formatTime(
                          message.timestamp,
                        )}
                      </time>
                    </div>

                    <p
                      className={`mt-1 whitespace-pre-wrap text-sm leading-6 ${
                        isUser
                          ? "text-white"
                          : "text-text dark:text-gray-100"
                      }`}
                    >
                      {message.content ||
                        (
                          message.status ===
                            "pending" ||
                          message.status ===
                            "streaming"
                            ? "Antwort wird erstellt …"
                            : ""
                        )}
                    </p>

                    {import.meta.env.DEV &&
                    !isUser ? (
                      <div className="mt-2 border-t border-border-soft pt-2 text-[10px] text-text-subtle dark:border-white/10 dark:text-gray-500">
                        <span>
                          Status:{" "}
                          {message.status}
                        </span>

                        {message.requestId ? (
                          <span className="ml-3">
                            Request:{" "}
                            {message.requestId}
                          </span>
                        ) : null}
                      </div>
                    ) : null}
                  </div>
                </article>
              );
            },
          )
        )}

        {showTypingIndicator ? (
          <div className="flex animate-fade-in items-start gap-3">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-secondary-soft text-xs font-bold uppercase text-secondary dark:bg-secondary/20 dark:text-secondary">
              AI
            </div>

            <div className="max-w-[85%] rounded-2xl border border-border-soft bg-white/90 px-4 py-3 backdrop-blur-sm dark:border-white/10 dark:bg-slate-800/80">
              <div className="flex items-center gap-1">
                <span className="h-2 w-2 animate-pulse rounded-full bg-primary/60 dark:bg-primary/40" />
                <span className="animation-delay-200 h-2 w-2 animate-pulse rounded-full bg-primary/60 dark:bg-primary/40" />
                <span className="animation-delay-400 h-2 w-2 animate-pulse rounded-full bg-primary/60 dark:bg-primary/40" />

                <span className="ml-1 text-sm text-text-muted dark:text-gray-400">
                  tippt …
                </span>
              </div>
            </div>
          </div>
        ) : null}

        <div ref={messagesEndRef} />
      </div>

      {error ? (
        <div
          className="shrink-0 border-t border-danger/20 bg-danger-soft px-4 py-2 text-sm text-danger dark:bg-danger/10 dark:text-danger"
          role="alert"
        >
          <span className="font-medium">
            Fehler:
          </span>{" "}
          {error}
        </div>
      ) : null}

      <form
        onSubmit={submit}
        className="shrink-0 border-t border-border bg-white/80 p-4 backdrop-blur-sm dark:border-white/10 dark:bg-slate-900/60"
      >
        <div className="flex gap-2">
          <label
            htmlFor="chat-message-input"
            className="sr-only"
          >
            Nachricht
          </label>

          <input
            id="chat-message-input"
            className="min-w-0 flex-1 rounded-xl border border-border-soft bg-surface-muted px-4 py-2.5 text-text outline-none transition placeholder:text-text-subtle focus:border-primary focus:ring-4 focus:ring-primary-soft disabled:opacity-60 dark:border-white/10 dark:bg-slate-800/40 dark:text-white dark:placeholder:text-gray-500 dark:focus:ring-primary/20"
            value={input}
            onChange={(event) =>
              setInput(
                event.target.value,
              )
            }
            onKeyDown={
              handleInputKeyDown
            }
            placeholder="Nachricht eingeben …"
            autoComplete="off"
            disabled={loading}
            maxLength={
              MAX_MESSAGE_LENGTH
            }
          />

          {loading ? (
            <button
              type="button"
              className="shrink-0 rounded-xl border border-border-soft bg-surface px-4 py-2.5 font-medium text-text-soft transition hover:bg-surface-hover hover:shadow-sm dark:border-white/10 dark:bg-slate-800/60 dark:text-gray-300 dark:hover:bg-slate-700/60"
              onClick={stopGeneration}
              aria-label="Antwort abbrechen"
              title="Antwort abbrechen"
            >
              <svg
                className="h-5 w-5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                xmlns="http://www.w3.org/2000/svg"
                aria-hidden="true"
              >
                <rect
                  x="6"
                  y="6"
                  width="12"
                  height="12"
                  rx="1"
                />
              </svg>
            </button>
          ) : (
            <button
              type="submit"
              className="shrink-0 rounded-xl bg-primary px-5 py-2.5 font-medium text-white shadow-glow transition hover:bg-primary-hover hover:shadow-primary-glow focus:outline-none focus:ring-4 focus:ring-primary-soft disabled:cursor-not-allowed disabled:opacity-50 dark:bg-primary-dark dark:hover:bg-primary-dark-hover"
              disabled={!input.trim()}
              aria-label="Nachricht senden"
              title="Nachricht senden"
            >
              <svg
                className="h-5 w-5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                xmlns="http://www.w3.org/2000/svg"
                aria-hidden="true"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
                />
              </svg>
            </button>
          )}
        </div>

        <div className="mt-2 flex items-center justify-between gap-4 text-xs text-text-muted dark:text-gray-500">
          <p>
            Enter zum Senden. Während der
            Antwort kann mit Escape
            abgebrochen werden.
          </p>

          <span>
            {input.length.toLocaleString(
              "de-DE",
            )}
            /
            {MAX_MESSAGE_LENGTH.toLocaleString(
              "de-DE",
            )}
          </span>
        </div>
      </form>
    </section>
  );
}