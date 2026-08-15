// F:\Kernschmied\frontend\src\components\widgets\ChatWidget.tsx

import React, { useEffect, useState } from 'react';
import { MessageSquare, RefreshCw, AlertCircle, User, Bot } from 'lucide-react';
import IconBadge from '../common/IconBadge';

interface ChatWidgetProps {
  widget?: any;
  nodeId?: string;
}

interface ChatMessage {
  id?: string;
  user?: string;
  role?: 'user' | 'assistant' | 'system';
  text?: string;
  message?: string;
  time?: string;
  timestamp?: string;
}

export default function ChatWidget({ widget, nodeId }: ChatWidgetProps) {
  const [messages, setMessages] = useState<ChatMessage[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const loadMessages = async (showRefresh = false) => {
    if (showRefresh) setIsRefreshing(true);
    setError(null);

    try {
      const res = await fetch('/api/v1/chat/recent');
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}: ${res.statusText}`);
      }
      const j = await res.json();
      const items = Array.isArray(j) ? j : j.items ?? [];
      setMessages(
        items.map((m: any) => ({
          id: m.id,
          user: m.author_name
            ?? m.ui_context?.assistant_display_name
            ?? m.user
            ?? m.sender
            ?? (m.role === 'assistant' ? 'KI' : 'Benutzer'),
          role: m.role ?? (m.user === 'assistant' ? 'assistant' : 'user'),
          text: m.text ?? m.message ?? String(m),
          time: m.time ?? m.timestamp ?? m.created_at,
        }))
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Chat‑Nachrichten konnten nicht geladen werden.');
      setMessages(null);
    } finally {
      if (showRefresh) setIsRefreshing(false);
      setLoading(false);
    }
  };

  useEffect(() => {
    setLoading(true);
    void loadMessages(false);
  }, []);

  const formatTime = (time?: string) => {
    if (!time) return '—';
    try {
      return new Date(time).toLocaleString('de-DE', {
        dateStyle: 'short',
        timeStyle: 'short',
      });
    } catch {
      return time;
    }
  };

  const getInitials = (user?: string) => {
    if (!user) return '?';
    const parts = user.trim().split(/\s+/);
    if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
    return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
  };

  return (
    <div className="rounded-xl border border-border-soft bg-white/90 p-4 shadow-sm backdrop-blur-sm dark:border-white/10 dark:bg-slate-900/80">
      {/* Kopfzeile */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2.5">
          <IconBadge icon={<MessageSquare />} size="md" variant="primary" />
          <h3 className="text-sm font-semibold text-text dark:text-white">Chat</h3>
          {messages && (
            <span className="rounded-full bg-surface-muted px-2 py-0.5 text-xs text-text-muted dark:bg-slate-800 dark:text-gray-400">
              {messages.length}
            </span>
          )}
        </div>
        <button
          type="button"
          className="rounded-lg p-1.5 text-text-muted transition hover:bg-surface-hover hover:text-text focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary dark:text-gray-400 dark:hover:bg-slate-800 dark:hover:text-white"
          onClick={() => void loadMessages(true)}
          disabled={isRefreshing}
          aria-label="Chat neu laden"
          title="Neu laden"
        >
          <IconBadge icon={<RefreshCw className={isRefreshing ? 'animate-spin' : ''} />} size="sm" variant="default" />
        </button>
      </div>

      {/* Inhalt */}
      {loading ? (
        <div className="flex items-center gap-2 py-4 text-sm text-text-muted dark:text-gray-400">
          <span className="h-2 w-2 animate-pulse rounded-full bg-primary/60" />
          Lade Nachrichten …
        </div>
      ) : error ? (
        <div className="flex items-start gap-2 rounded-lg border border-danger/20 bg-danger-soft px-3 py-2 text-sm text-danger dark:border-danger/30 dark:bg-danger/10">
          <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      ) : messages && messages.length > 0 ? (
        <div className="flex flex-col gap-2.5 max-h-64 overflow-y-auto">
          {messages.slice(0, 12).map((msg, idx) => {
            const isUser = msg.role === 'user' || msg.user === 'Benutzer';
            const isAssistant = msg.role === 'assistant' || msg.user === 'Assistent';
            const displayName = isUser ? (msg.user ?? 'Benutzer') : isAssistant ? 'KI' : (msg.user ?? 'System');
            const initials = getInitials(displayName);

            return (
              <div
                key={msg.id ?? idx}
                className={[
                  'flex items-start gap-2.5',
                  isUser ? 'flex-row-reverse' : 'flex-row',
                ].join(' ')}
              >
                {/* Avatar */}
                <div className="shrink-0">
                  <IconBadge
                    icon={
                      isUser ? (
                        <User />
                      ) : isAssistant ? (
                        <Bot />
                      ) : (
                        <span className="text-xs font-bold uppercase">{initials}</span>
                      )
                    }
                    size="sm"
                    variant={isUser ? 'primary' : isAssistant ? 'secondary' : 'default'}
                  />
                </div>

                {/* Nachricht */}
                <div
                  className={[
                    'max-w-[75%] rounded-2xl px-3.5 py-2.5 shadow-sm',
                    isUser
                      ? 'bg-primary text-white dark:bg-primary-dark'
                      : isAssistant
                        ? 'border border-border-soft bg-white/80 dark:border-white/10 dark:bg-slate-800/60'
                        : 'border border-border-soft bg-surface-muted/50 dark:border-white/10 dark:bg-slate-800/30',
                  ].join(' ')}
                >
                  <div className="flex items-center justify-between gap-3">
                    <span
                      className={[
                        'text-xs font-medium',
                        isUser ? 'text-white/80' : 'text-text-muted dark:text-gray-400',
                      ].join(' ')}
                    >
                      {displayName}
                    </span>
                    <time
                      className={[
                        'shrink-0 text-[10px]',
                        isUser ? 'text-white/60' : 'text-text-muted dark:text-gray-500',
                      ].join(' ')}
                    >
                      {formatTime(msg.time)}
                    </time>
                  </div>
                  <p
                    className={[
                      'mt-1 text-sm leading-6 whitespace-pre-wrap wrap-break-word',
                      isUser ? 'text-white' : 'text-text dark:text-gray-100',
                    ].join(' ')}
                  >
                    {msg.text}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <div className="flex flex-col items-center gap-2 py-6 text-center">
          <IconBadge icon={<MessageSquare />} size="lg" variant="default" />
          <span className="text-sm text-text-muted dark:text-gray-400">Keine Chat‑Nachrichten gefunden.</span>
        </div>
      )}
    </div>
  );
}