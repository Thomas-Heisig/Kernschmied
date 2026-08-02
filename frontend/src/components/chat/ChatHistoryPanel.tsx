import React, { useEffect, useRef, useState } from 'react';
import { RefreshCw, Copy } from 'lucide-react';
import { useChatHistory, type ChatMessage } from '../../hooks/useChatHistory';

export default function ChatHistoryPanel({ onClose }: { onClose: () => void }) {
  const [conversationId, setConversationId] = useState('');
  const { loading, error, messages, fetchHistory } = useChatHistory();
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const panelRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === 'Escape') onClose();
    }
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [onClose]);

  useEffect(() => {
    function onMDown(e: MouseEvent) {
      if (!panelRef.current) return;
      if (!panelRef.current.contains(e.target as Node)) onClose();
    }
    document.addEventListener('mousedown', onMDown);
    return () => document.removeEventListener('mousedown', onMDown);
  }, [onClose]);

  async function copyText(id: string, text: string) {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedId(id);
      setTimeout(() => setCopiedId((v) => (v === id ? null : v)), 1500);
    } catch {
      /* ignore */
    }
  }

  function renderContent(msg: ChatMessage) {
    // split on fenced code blocks ```lang\n...```
    const parts: Array<{ type: 'text' | 'code'; text: string; lang?: string }> = [];
    const re = /```(.*?)\n([\s\S]*?)```/gm;
    let lastIndex = 0;
    let m;
    while ((m = re.exec(msg.content)) !== null) {
      if (m.index > lastIndex) {
        parts.push({ type: 'text', text: msg.content.substring(lastIndex, m.index) });
      }
      parts.push({ type: 'code', lang: m[1]?.trim() || undefined, text: m[2] });
      lastIndex = re.lastIndex;
    }
    if (lastIndex < msg.content.length) {
      parts.push({ type: 'text', text: msg.content.substring(lastIndex) });
    }

    return (
      <div className="space-y-2">
        {parts.map((p, i) =>
          p.type === 'text' ? (
            <div key={i} className="whitespace-pre-wrap text-sm">
              {p.text}
            </div>
          ) : (
            <div key={i} className="relative bg-gray-900 text-gray-100 rounded p-2 text-xs font-mono overflow-auto">
              <pre className="whitespace-pre-wrap">{p.text}</pre>
              <button
                className="absolute right-1 top-1 p-1 rounded bg-white/5 hover:bg-white/10 text-xs"
                onClick={() => copyText(msg.id + '-' + i, p.text)}
                aria-label="Copy code"
                type="button"
              >
                <Copy size={12} />
              </button>
            </div>
          )
        )}
      </div>
    );
  }

  return (
    <div ref={panelRef} className="fixed right-4 bottom-24 z-50 w-[min(720px,95%)] max-w-full rounded border bg-white p-4 shadow dark:bg-slate-800">
      <div className="flex items-center justify-between">
        <div className="flex items-baseline gap-3">
          <strong>Chat-Historie</strong>
          <span className="text-xs text-text-muted">{conversationId ? `(${conversationId})` : ''}</span>
        </div>
        <div className="flex items-center gap-2">
          <button
            className="text-sm text-gray-500 hover:text-gray-700"
            onClick={() => fetchHistory(conversationId)}
            disabled={!conversationId || loading}
            title="Neu laden"
          >
            <RefreshCw size={16} />
          </button>
          <button className="text-sm text-gray-500" onClick={onClose}>✕</button>
        </div>
      </div>

      <div className="mt-3">
        <div className="flex gap-2">
          <input
            className="flex-1 rounded border px-2 py-1 bg-white dark:bg-slate-800"
            placeholder="Conversation ID eingeben"
            value={conversationId}
            onChange={(e) => setConversationId(e.target.value)}
          />
          <button
            className="px-3 py-1 rounded bg-sky-600 text-white disabled:opacity-50"
            onClick={() => fetchHistory(conversationId)}
            disabled={!conversationId || loading}
          >
            {loading ? 'Lädt…' : 'Laden'}
          </button>
        </div>

        {error ? <div className="mt-2 text-sm text-red-600">{error}</div> : null}

        <div className="mt-3 max-h-72 overflow-auto text-sm space-y-3">
          {messages?.length ? (
            messages.map((m) => {
              const isUser = m.role === 'user';
              return (
                <div key={m.id} className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
                  <div className={`max-w-[86%] rounded-lg p-3 ${isUser ? 'bg-sky-50 text-sky-900' : 'bg-gray-100 text-gray-900'} shadow-sm` }>
                    <div className="flex items-center justify-between gap-2 mb-1">
                      <div className="text-xs text-text-muted">
                        <span className="font-medium mr-2">{m.role}</span>
                        <span className="text-[11px] text-gray-500">{m.position} · {new Date(m.created_at).toLocaleString()}</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <button
                          className="text-xs text-gray-500 hover:text-gray-700"
                          onClick={() => copyText(m.id, m.content)}
                          title="Nachricht kopieren"
                        >
                          {copiedId === m.id ? '✔' : <Copy size={12} />}
                        </button>
                      </div>
                    </div>

                    {renderContent(m)}
                  </div>
                </div>
              );
            })
          ) : (
            <div className="text-sm text-text-muted">Keine Nachrichten geladen.</div>
          )}
        </div>
      </div>
    </div>
  );
}
