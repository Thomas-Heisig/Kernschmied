import { useCallback, useState } from 'react';

export interface ChatMessage {
  id: string;
  role: string;
  content: string;
  metadata: Record<string, any>;
  position: number;
  created_at: string;
}

export function useChatHistory() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[] | null>(null);

  const fetchHistory = useCallback(async (conversationId: string) => {
    setLoading(true);
    setError(null);
    setMessages(null);

    try {
      const res = await fetch(`/api/v1/chats/${encodeURIComponent(conversationId)}/messages`, {
        cache: 'no-store',
      });

      if (!res.ok) {
        const txt = await res.text();
        throw new Error(`${res.status} ${res.statusText} ${txt}`);
      }

      const data = (await res.json()) as ChatMessage[];
      setMessages(data);
      return data;
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
