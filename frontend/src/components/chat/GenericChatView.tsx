/// <reference types="react" />

import React, {
  FormEvent,
  KeyboardEvent,
  useEffect,
  useRef,
  useState,
} from "react";

import { API_BASE_URL } from "../../api/client";

type GenericChatViewProps = {
  title: string;
};

type ChatMessage = {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
};

type StreamTokenPayload = {
  content?: unknown;
};

function createMessageId(): string {
  return crypto.randomUUID();
}

function normalizeSseBuffer(value: string): string {
  return value.replace(/\r\n/g, "\n").replace(/\r/g, "\n");
}

function parseSseEvent(chunk: string): {
  event: string;
  data: string;
} | null {
  let event = "message";
  const dataLines: string[] = [];

  for (const line of chunk.split("\n")) {
    if (!line || line.startsWith(":")) {
      continue;
    }

    const separatorIndex = line.indexOf(":");

    let field: string;
    let value: string;

    if (separatorIndex === -1) {
      field = line;
      value = "";
    } else {
      field = line.slice(0, separatorIndex);
      value = line.slice(separatorIndex + 1);

      if (value.startsWith(" ")) {
        value = value.slice(1);
      }
    }

    if (field === "event") {
      event = value;
    }

    if (field === "data") {
      dataLines.push(value);
    }
  }

  if (dataLines.length === 0) {
    return null;
  }

  return {
    event,
    data: dataLines.join("\n"),
  };
}

function extractTokenContent(data: string): string {
  if (!data || data === "[DONE]") {
    return "";
  }

  try {
    const parsed = JSON.parse(data) as StreamTokenPayload;

    return typeof parsed.content === "string" ? parsed.content : "";
  } catch {
    return data;
  }
}

export function GenericChatView({
  title,
}: GenericChatViewProps): React.JSX.Element {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const abortControllerRef = useRef<AbortController | null>(null);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({
      behavior: "smooth",
      block: "end",
    });
  }, [messages]);

  useEffect(() => {
    return () => {
      abortControllerRef.current?.abort();
    };
  }, []);

  function appendAssistantContent(
    assistantMessageId: string,
    content: string,
  ): void {
    if (!content) {
      return;
    }

    setMessages((currentMessages) =>
      currentMessages.map((message) =>
        message.id === assistantMessageId
          ? {
              ...message,
              content: message.content + content,
            }
          : message,
      ),
    );
  }

  function replaceAssistantContent(
    assistantMessageId: string,
    content: string,
  ): void {
    setMessages((currentMessages) =>
      currentMessages.map((message) =>
        message.id === assistantMessageId
          ? {
              ...message,
              content,
            }
          : message,
      ),
    );
  }

  async function processSseStream(
    response: Response,
    assistantMessageId: string,
  ): Promise<void> {
    if (!response.body) {
      throw new Error("Der Server hat keinen lesbaren Datenstrom geliefert.");
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");

    let buffer = "";

    async function processChunk(chunk: string): Promise<void> {
      const parsedEvent = parseSseEvent(chunk);

      if (!parsedEvent) {
        return;
      }

      if (
        parsedEvent.event === "done" ||
        parsedEvent.data === "[DONE]"
      ) {
        return;
      }

      if (parsedEvent.event === "error") {
        let message = "Beim Verarbeiten der Nachricht ist ein Fehler aufgetreten.";

        try {
          const parsed = JSON.parse(parsedEvent.data) as {
            message?: unknown;
            detail?: unknown;
          };

          if (typeof parsed.message === "string") {
            message = parsed.message;
          } else if (typeof parsed.detail === "string") {
            message = parsed.detail;
          }
        } catch {
          if (parsedEvent.data.trim()) {
            message = parsedEvent.data.trim();
          }
        }

        throw new Error(message);
      }

      if (
        parsedEvent.event === "token" ||
        parsedEvent.event === "message"
      ) {
        const content = extractTokenContent(parsedEvent.data);
        appendAssistantContent(assistantMessageId, content);
      }
    }

    while (true) {
      const { value, done } = await reader.read();

      if (done) {
        buffer += decoder.decode();
        break;
      }

      buffer += decoder.decode(value, {
        stream: true,
      });

      buffer = normalizeSseBuffer(buffer);

      const chunks = buffer.split("\n\n");
      buffer = chunks.pop() ?? "";

      for (const chunk of chunks) {
        await processChunk(chunk);
      }
    }

    const remainingChunk = normalizeSseBuffer(buffer).trim();

    if (remainingChunk) {
      await processChunk(remainingChunk);
    }
  }

  async function submit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();

    const prompt = input.trim();

    if (!prompt || loading) {
      return;
    }

    const userMessage: ChatMessage = {
      id: createMessageId(),
      role: "user",
      content: prompt,
    };

    const assistantMessage: ChatMessage = {
      id: createMessageId(),
      role: "assistant",
      content: "",
    };

    setMessages((currentMessages) => [
      ...currentMessages,
      userMessage,
      assistantMessage,
    ]);

    setInput("");
    setError(null);
    setLoading(true);

    const abortController = new AbortController();
    abortControllerRef.current = abortController;

    try {
      const response = await fetch(`${API_BASE_URL}/chat/stream`, {
        method: "POST",
        headers: {
          Accept: "text/event-stream",
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message: prompt,
        }),
        signal: abortController.signal,
      });

      if (!response.ok) {
        let message = `Die Anfrage ist fehlgeschlagen (${response.status}).`;

        try {
          const body = (await response.json()) as {
            message?: unknown;
            detail?: unknown;
          };

          if (typeof body.message === "string") {
            message = body.message;
          } else if (typeof body.detail === "string") {
            message = body.detail;
          }
        } catch {
          const responseText = await response.text();

          if (responseText.trim()) {
            message = responseText.trim();
          }
        }

        throw new Error(message);
      }

      await processSseStream(response, assistantMessage.id);

      setMessages((currentMessages) =>
        currentMessages.map((message) => {
          if (
            message.id === assistantMessage.id &&
            message.content.trim() === ""
          ) {
            return {
              ...message,
              content: "Der Server hat keine Antwort geliefert.",
            };
          }

          return message;
        }),
      );
    } catch (caughtError) {
      if (
        caughtError instanceof DOMException &&
        caughtError.name === "AbortError"
      ) {
        replaceAssistantContent(
          assistantMessage.id,
          "Die Antwort wurde abgebrochen.",
        );
        return;
      }

      const message =
        caughtError instanceof Error
          ? caughtError.message
          : "Die Nachricht konnte nicht gesendet werden.";

      setError(message);
      replaceAssistantContent(
        assistantMessage.id,
        `Fehler: ${message}`,
      );
    } finally {
      if (abortControllerRef.current === abortController) {
        abortControllerRef.current = null;
      }

      setLoading(false);
    }
  }

  function stopGeneration(): void {
    abortControllerRef.current?.abort();
  }

  function handleInputKeyDown(
    event: KeyboardEvent<HTMLInputElement>,
  ): void {
    if (event.key === "Escape" && loading) {
      stopGeneration();
    }
  }

  return (
    <section
      className="flex h-full min-h-0 flex-col bg-slate-50"
      aria-label={`Chat: ${title}`}
    >
      <header className="shrink-0 border-b border-slate-200 bg-white px-5 py-3">
        <h1 className="font-semibold text-slate-900">{title}</h1>
      </header>

      <div
        className="min-h-0 flex-1 space-y-4 overflow-y-auto p-5"
        aria-live="polite"
        aria-busy={loading}
      >
        {messages.length === 0 ? (
          <div className="flex h-full items-center justify-center">
            <p className="text-sm text-slate-500">
              Noch keine Nachrichten.
            </p>
          </div>
        ) : (
          messages.map((message) => {
            const isUser = message.role === "user";

            return (
              <article
                key={message.id}
                className={`flex ${
                  isUser ? "justify-end" : "justify-start"
                }`}
              >
                <div
                  className={`max-w-[85%] rounded-xl px-4 py-3 shadow-sm ${
                    isUser
                      ? "bg-slate-900 text-white"
                      : "border border-slate-200 bg-white text-slate-900"
                  }`}
                >
                  <div className="mb-1 text-xs font-semibold opacity-70">
                    {isUser ? "Du" : "Assistent"}
                  </div>

                  <p className="whitespace-pre-wrap wrap-break-words text-sm leading-6">
                    {message.content ||
                      (loading && message.role === "assistant"
                        ? "Antwort wird erstellt …"
                        : "")}
                  </p>
                </div>
              </article>
            );
          })
        )}

        <div ref={messagesEndRef} />
      </div>

      {error ? (
        <div
          className="shrink-0 border-t border-red-200 bg-red-50 px-4 py-2 text-sm text-red-700"
          role="alert"
        >
          {error}
        </div>
      ) : null}

      <form
        onSubmit={submit}
        className="shrink-0 border-t border-slate-200 bg-white p-4"
      >
        <div className="flex gap-2">
          <label htmlFor="chat-message-input" className="sr-only">
            Nachricht
          </label>

          <input
            id="chat-message-input"
            className="min-w-0 flex-1 rounded-lg border border-slate-300 px-3 py-2 text-slate-900 outline-none transition focus:border-slate-500 focus:ring-2 focus:ring-slate-200 disabled:cursor-not-allowed disabled:bg-slate-100"
            value={input}
            onChange={(event) => setInput(event.target.value)}
            onKeyDown={handleInputKeyDown}
            placeholder="Nachricht eingeben …"
            autoComplete="off"
            disabled={loading}
          />

          {loading ? (
            <button
              type="button"
              className="rounded-lg border border-slate-300 bg-white px-4 py-2 font-medium text-slate-700 transition hover:bg-slate-100 focus:outline-none focus:ring-2 focus:ring-slate-300"
              onClick={stopGeneration}
            >
              Stoppen
            </button>
          ) : (
            <button
              type="submit"
              className="rounded-lg bg-slate-900 px-4 py-2 font-medium text-white transition hover:bg-slate-700 focus:outline-none focus:ring-2 focus:ring-slate-400 disabled:cursor-not-allowed disabled:opacity-50"
              disabled={!input.trim()}
            >
              Senden
            </button>
          )}
        </div>

        <p className="mt-2 text-xs text-slate-500">
          Enter zum Senden. Während der Antwort kann mit Escape abgebrochen
          werden.
        </p>
      </form>
    </section>
  );
}