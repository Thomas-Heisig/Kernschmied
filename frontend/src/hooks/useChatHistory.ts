import { useCallback, useState } from 'react';

export interface ChatMessage {
  id: string;
  role: string;
  // Some backends return `content`, others `text` — accept both.
  content?: string;
  text?: string;
  metadata?: Record<string, any>;
  position?: number;
  created_at: string;
}

export interface ChatHistoryResponse {
  schema_version: string;
  conversation_id: string;
  items: ChatMessage[];
  has_more?: boolean;
  next_cursor?: number | null;
}

export function useChatHistory() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[] | null>(null);

  const fetchHistory = useCallback(async (conversationId: string) => {
    setLoading(true);
    setError(null);

    try {
      const res = await fetch(`/api/v1/chats/${encodeURIComponent(conversationId)}/messages`, {
        cache: 'no-store',
      });

      if (!res.ok) {
        const txt = await res.text();
        throw new Error(`${res.status} ${res.statusText} ${txt}`);
      }

      const data = (await res.json()) as ChatHistoryResponse;

      // Return canonical items array. The backend returns a wrapped object
      // containing `items` and metadata (schema_version, has_more, ...).
      const items = Array.isArray(data?.items) ? data.items : [];
      setMessages(items);
      return items;
    } catch (err: any) {
      setError(err?.message ?? String(err));
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    loading,
    error,
    messages,
    fetchHistory,
  } as const;
}
