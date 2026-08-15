// F:\Kernschmied\frontend\src\components\chat\ChatHistoryPanel.tsx

import React, { lazy, Suspense, useEffect, useRef, useState } from 'react';
import { RefreshCw, Copy, X } from 'lucide-react';
import { useChatHistory } from '../../hooks/useChatHistory';
import IconBadge from '../common/IconBadge';

const ChatMessageContent = lazy(() => import('./ChatMessageContent'));

export default function ChatHistoryPanel({ onClose }: { onClose: () => void }) {
  const [conversationId, setConversationId] = useState('');
  const { loading, error, messages, fetchHistory } = useChatHistory();
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const panelRef = useRef<HTMLDivElement | null>(null);

  // ESC schließen
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [onClose]);

  // Klick außerhalb schließen
  useEffect(() => {
    const onMouseDown = (e: MouseEvent) => {
      if (!panelRef.current) return;
      if (!panelRef.current.contains(e.target as Node)) onClose();
    };
    document.addEventListener('mousedown', onMouseDown);
    return () => document.removeEventListener('mousedown', onMouseDown);
  }, [onClose]);

  async function copyText(id: string, text: string) {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedId(id);
      setTimeout(() => setCopiedId((prev) => (prev === id ? null : prev)), 1500);
    } catch {
      /* ignore */
    }
  }

  return (
    <div
      ref={panelRef}
      className="fixed right-4 bottom-24 z-50 w-[min(720px,95%)] max-w-full rounded-xl border border-border-soft bg-white/95 shadow-xl backdrop-blur-sm dark:border-white/10 dark:bg-slate-900/95 dark:backdrop-blur-sm"
      role="dialog"
      aria-label="Chat-Historie"
    >
      {/* Kopfzeile */}
      <div className="flex items-center justify-between border-b border-border-soft px-5 py-3 dark:border-white/10">
        <div className="flex items-baseline gap-3">
          <h2 className="text-base font-semibold text-text-soft dark:text-gray-200">Chat-Historie</h2>
          {conversationId && (
            <span className="text-xs text-text-muted dark:text-gray-500">({conversationId})</span>
          )}
        </div>

        <div className="flex items-center gap-2">
          <button
            className="rounded p-1.5 text-text-muted hover:bg-surface-hover hover:text-text focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary disabled:opacity-40 dark:text-gray-500 dark:hover:bg-slate-800 dark:hover:text-gray-300"
            onClick={() => fetchHistory(conversationId)}
            disabled={!conversationId || loading}
            aria-label="Historie neu laden"
            title="Neu laden"
          >
            <IconBadge icon={<RefreshCw />} size="sm" variant="default" />
          </button>

          <button
            className="rounded p-1.5 text-text-muted hover:bg-surface-hover hover:text-text focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary dark:text-gray-500 dark:hover:bg-slate-800 dark:hover:text-gray-300"
            onClick={onClose}
            aria-label="Schließen"
            title="Schließen"
          >
            <IconBadge icon={<X />} size="sm" variant="default" />
          </button>
        </div>
      </div>

      {/* Inhalt */}
      <div className="p-5">
        {/* Eingabezeile */}
        <div className="flex gap-2">
          <input
            className="flex-1 rounded-lg border border-border-soft bg-surface-muted px-4 py-2 text-sm text-text outline-none placeholder:text-text-subtle focus:border-primary focus:ring-4 focus:ring-primary-soft dark:border-white/10 dark:bg-slate-800/50 dark:text-white dark:placeholder:text-gray-500 dark:focus:ring-primary/20"
            placeholder="Conversation ID eingeben"
            value={conversationId}
            onChange={(e) => setConversationId(e.target.value)}
            aria-label="Conversation ID"
          />
          <button
            className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-white shadow-glow transition hover:bg-primary-hover hover:shadow-primary-glow disabled:cursor-not-allowed disabled:opacity-40 dark:bg-primary-dark dark:hover:bg-primary-dark-hover"
            onClick={() => fetchHistory(conversationId)}
            disabled={!conversationId || loading}
          >
            {loading ? 'Lädt…' : 'Laden'}
          </button>
        </div>

        {/* Fehleranzeige */}
        {error && (
          <div className="mt-3 rounded-lg bg-danger-soft px-4 py-2 text-sm text-danger dark:bg-danger/10">
            {error}
          </div>
        )}

        {/* Nachrichtenliste */}
        <div className="mt-4 max-h-80 overflow-y-auto overscroll-contain space-y-4 pr-1">
          {messages?.length ? (
            messages.map((m) => {
              const isUser = m.role === 'user';
              return (
                <div
                  key={m.id}
                  className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[86%] rounded-2xl px-4 py-3 shadow-sm ${
                      isUser
                        ? 'bg-slate-800 text-white ring-1 ring-slate-950/10 dark:bg-primary-dark dark:ring-white/10'
                        : 'border border-border-soft bg-white/90 dark:border-white/10 dark:bg-slate-800/80'
                    }`}
                  >
                    {/* Kopf der Nachricht */}
                    <div className="mb-1 flex items-center justify-between gap-3">
                      <div className="flex items-center gap-2 text-xs">
                        <span
                          className={`font-medium ${
                            isUser ? 'text-white/80' : 'text-text-muted dark:text-gray-400'
                          }`}
                        >
                          {m.role}
                        </span>
                        <span
                          className={`text-[11px] ${
                            isUser ? 'text-white/60' : 'text-text-subtle dark:text-gray-500'
                          }`}
                        >
                          {m.position} · {new Date(m.created_at).toLocaleString()}
                        </span>
                      </div>
                      <button
                        className="rounded p-1 text-xs transition hover:bg-white/10 dark:hover:bg-slate-700/50"
                        onClick={() => copyText(m.id, m.content ?? m.text ?? '')}
                        aria-label="Nachricht kopieren"
                        title="Nachricht kopieren"
                      >
                        {copiedId === m.id ? (
                          <span className="text-green-400">✔</span>
                        ) : (
                          <IconBadge icon={<Copy />} size="sm" variant="default" />
                        )}
                      </button>
                    </div>

                    {/* Inhalt */}
                    <div className={isUser ? '[&_.chat-message-content]:text-white [&_.chat-message-content_a]:text-cyan-200' : 'text-slate-900 dark:text-gray-100'}>
                      <Suspense fallback={<p className="whitespace-pre-wrap text-sm leading-6">{m.content ?? m.text ?? ''}</p>}>
                        <ChatMessageContent content={m.content ?? m.text ?? ''} isAssistant={!isUser} />
                      </Suspense>
                    </div>
                  </div>
                </div>
              );
            })
          ) : (
            <div className="text-sm text-text-muted dark:text-gray-500">
              Keine Nachrichten geladen.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}