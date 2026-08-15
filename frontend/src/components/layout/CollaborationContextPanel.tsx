import { useCallback, useEffect, useMemo, useState } from 'react';
import { Archive, ExternalLink, Mail, RefreshCw, Trash2, Users } from 'lucide-react';
import {
  loadOnlineUsers,
} from '../../api/mentions';
import type { MentionCandidate } from '../../api/mentions';
import {
  loadMailboxMessages,
  loadMyMailbox,
  deleteMailboxMessage,
  updateMailboxMessage,
} from '../../api/mailbox';
import type { MailboxMessage, UserMailbox } from '../../api/mailbox';
import IconBadge from '../common/IconBadge';

interface CollaborationContextPanelProps {
  hierarchyNodeId: string;
  onNavigateToNode?: (id: string) => void;
}

export default function CollaborationContextPanel({
  hierarchyNodeId,
  onNavigateToNode,
}: CollaborationContextPanelProps) {
  const [onlineUsers, setOnlineUsers] = useState<MentionCandidate[]>([]);
  const [mailbox, setMailbox] = useState<UserMailbox | null>(null);
  const [messages, setMessages] = useState<MailboxMessage[]>([]);
  const [messageFilter, setMessageFilter] = useState<'all' | 'unread' | 'read' | 'archived'>('all');
  const [sortDirection, setSortDirection] = useState<'newest' | 'oldest'>('newest');
  const [loading, setLoading] = useState(false);

  const visibleMessages = useMemo(
    () => messages
      .filter((message) => messageFilter === 'all' || message.status === messageFilter)
      .sort((left, right) => {
        const delta = Date.parse(right.createdAt) - Date.parse(left.createdAt);
        return sortDirection === 'newest' ? delta : -delta;
      }),
    [messageFilter, messages, sortDirection],
  );

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const [nextOnlineUsers, nextMailbox, nextMessages] = await Promise.all([
        loadOnlineUsers(hierarchyNodeId),
        loadMyMailbox(),
        loadMailboxMessages(),
      ]);
      setOnlineUsers(nextOnlineUsers);
      setMailbox(nextMailbox);
      setMessages(nextMessages);
    } catch {
      // Collaboration context is supplementary and must not block node context.
    } finally {
      setLoading(false);
    }
  }, [hierarchyNodeId]);

  useEffect(() => {
    void refresh();
    const interval = window.setInterval(() => void refresh(), 30_000);
    return () => window.clearInterval(interval);
  }, [refresh]);

  async function openMessage(message: MailboxMessage): Promise<void> {
    if (message.status === 'unread') {
      const updated = await updateMailboxMessage(message.id, 'read');
      setMessages((current) =>
        current.map((item) => (item.id === message.id ? updated : item)),
      );
    }
    if (message.hierarchyNodeId) onNavigateToNode?.(message.hierarchyNodeId);
  }

  async function archiveMessage(message: MailboxMessage): Promise<void> {
    await updateMailboxMessage(message.id, 'archived');
    setMessages((current) => current.filter((item) => item.id !== message.id));
  }

  async function deleteMessage(message: MailboxMessage): Promise<void> {
    await deleteMailboxMessage(message.id);
    setMessages((current) => current.filter((item) => item.id !== message.id));
  }

  return (
    <div className="space-y-4">
      <section className="rounded-lg border border-border-soft p-3 dark:border-white/10">
        <div className="flex items-center justify-between gap-2">
          <h3 className="flex items-center gap-2 text-xs font-semibold tracking-wide text-text-muted uppercase">
            <IconBadge icon={<Users />} size="sm" variant="default" />
            Online
          </h3>
          <button
            type="button"
            onClick={() => void refresh()}
            className="rounded p-1 text-text-muted hover:bg-surface-hover"
            aria-label="Online-Liste aktualisieren"
            title="Aktualisieren"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
        {onlineUsers.length === 0 ? (
          <p className="mt-2 text-xs text-text-muted">Keine weiteren Benutzer online.</p>
        ) : (
          <ul className="mt-2 space-y-2">
            {onlineUsers.map((candidate) => (
              <li key={candidate.userId} className="flex items-center gap-2 text-sm">
                <span className="h-2.5 w-2.5 rounded-full bg-emerald-500" aria-label="Online" />
                <span className="min-w-0 truncate">{candidate.displayName}</span>
                <span className="ml-auto truncate text-xs text-text-muted">@{candidate.username}</span>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="rounded-lg border border-border-soft p-3 dark:border-white/10">
        <div className="flex items-center justify-between gap-2">
          <h3 className="flex items-center gap-2 text-xs font-semibold tracking-wide text-text-muted uppercase">
            <IconBadge icon={<Mail />} size="sm" variant="default" />
            Postfach
          </h3>
          {messages.length > 0 ? (
            <span className="rounded-full bg-primary px-2 py-0.5 text-[11px] font-semibold text-white">
              {messages.filter((message) => message.status === 'unread').length}
            </span>
          ) : null}
        </div>
        {mailbox ? (
          <div className="mt-2 border-b border-border-soft pb-2 text-xs text-text-muted">
            <div className="truncate" title={mailbox.internalAddress}>{mailbox.internalAddress}</div>
            <div>{mailbox.emailReady ? `E-Mail aktiv · ${mailbox.externalEmail}` : 'E-Mail vorbereitet, noch nicht aktiviert'}</div>
          </div>
        ) : null}
        <div className="mt-2 grid grid-cols-2 gap-2">
          <label className="text-xs text-text-muted">
            Ansicht
            <select className="mt-1 w-full rounded border border-border-soft bg-surface px-2 py-1" value={messageFilter} onChange={(event) => setMessageFilter(event.target.value as typeof messageFilter)}>
              <option value="all">Alle</option>
              <option value="unread">Ungelesen</option>
              <option value="read">Gelesen</option>
              <option value="archived">Archiv</option>
            </select>
          </label>
          <label className="text-xs text-text-muted">
            Sortierung
            <select className="mt-1 w-full rounded border border-border-soft bg-surface px-2 py-1" value={sortDirection} onChange={(event) => setSortDirection(event.target.value as typeof sortDirection)}>
              <option value="newest">Neueste zuerst</option>
              <option value="oldest">Älteste zuerst</option>
            </select>
          </label>
        </div>
        {visibleMessages.length === 0 ? (
          <p className="mt-2 text-xs text-text-muted">Keine neuen Nachrichten.</p>
        ) : (
          <ul className="mt-2 max-h-80 space-y-3 overflow-y-auto pr-1">
            {visibleMessages.map((message) => (
              <li
                key={message.id}
                className={`rounded-md border p-2 ${
                  message.status === 'unread'
                    ? 'border-primary/40 bg-primary-soft'
                    : 'border-border-soft'
                }`}
              >
                <div className="text-xs font-semibold">{message.senderName ?? message.subject}</div>
                <p className="mt-1 line-clamp-3 text-xs text-text-soft">{message.body}</p>
                <div className="mt-2 flex gap-2">
                  <button
                    type="button"
                    onClick={() => void openMessage(message)}
                    className="inline-flex items-center gap-1 rounded border border-border-soft px-2 py-1 text-xs hover:bg-surface-hover"
                  >
                    <ExternalLink className="h-3.5 w-3.5" /> Öffnen
                  </button>
                  <button
                    type="button"
                    onClick={() => void archiveMessage(message)}
                    className="inline-flex items-center gap-1 rounded border border-border-soft px-2 py-1 text-xs hover:bg-surface-hover"
                  >
                    <Archive className="h-3.5 w-3.5" /> Archivieren
                  </button>
                  <button
                    type="button"
                    onClick={() => void deleteMessage(message)}
                    className="inline-flex items-center gap-1 rounded border border-danger/30 px-2 py-1 text-xs text-danger hover:bg-danger-soft"
                  >
                    <Trash2 className="h-3.5 w-3.5" /> Löschen
                  </button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
