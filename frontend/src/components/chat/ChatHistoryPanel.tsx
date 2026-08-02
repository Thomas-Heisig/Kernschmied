import React, { useState } from 'react';
import { useChatHistory } from '../../hooks/useChatHistory';

export default function ChatHistoryPanel({ onClose }: { onClose: () => void }) {
  const [conversationId, setConversationId] = useState('');
  const { loading, error, messages, fetchHistory } = useChatHistory();

  return (
    <div className="fixed right-4 bottom-24 z-50 w-[min(720px,95%)] max-w-full rounded border bg-white p-4 shadow dark:bg-slate-800">
      <div className="flex items-center justify-between">
        <strong>Chat-Historie anzeigen</strong>
        <button className="text-sm text-gray-500" onClick={onClose}>✕</button>
      </div>

      <div className="mt-3">
        <div className="flex gap-2">
          <input
            className="flex-1 rounded border px-2 py-1"
            placeholder="Conversation ID eingeben"
            value={conversationId}
            onChange={(e) => setConversationId(e.target.value)}
          />
          <button
            className="px-3 py-1 rounded bg-sky-600 text-white"
            onClick={() => fetchHistory(conversationId)}
            disabled={!conversationId || loading}
          >
            {loading ? 'Lädt…' : 'Laden'}
          </button>
        </div>

        {error ? <div className="mt-2 text-sm text-red-600">{error}</div> : null}

        <div className="mt-3 max-h-64 overflow-auto text-sm">
          {messages?.length ? (
            messages.map((m) => (
              <div key={m.id} className="mb-2">
                <div className="text-xs text-text-muted">{m.position} · {new Date(m.created_at).toLocaleString()}</div>
                <div className="font-medium">{m.role}</div>
                <div className="whitespace-pre-wrap">{m.content}</div>
              </div>
            ))
          ) : (
            <div className="text-sm text-text-muted">Keine Nachrichten geladen.</div>
          )}
        </div>
      </div>
    </div>
  );
}
