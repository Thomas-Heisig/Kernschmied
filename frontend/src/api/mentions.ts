import { apiGet, apiPatch } from './client';

export interface MentionCandidate {
  userId: string;
  username: string;
  displayName: string;
  online: boolean;
  isAdministrator: boolean;
}

export type MentionStatus = 'unread' | 'read' | 'answered' | 'closed';

export interface UserMention {
  id: string;
  messageId: string;
  conversationId: string;
  hierarchyNodeId: string;
  senderUserId: string;
  senderName: string;
  targetUserId: string;
  mentionText: string;
  status: MentionStatus;
  createdAt: string;
  readAt: string | null;
  answeredAt: string | null;
  closedAt: string | null;
}

function normalizeCandidate(raw: Record<string, unknown>): MentionCandidate {
  return {
    userId: String(raw.user_id),
    username: String(raw.username),
    displayName: String(raw.display_name),
    online: Boolean(raw.online),
    isAdministrator: Boolean(raw.is_administrator),
  };
}

function normalizeMention(raw: Record<string, unknown>): UserMention {
  return {
    id: String(raw.id),
    messageId: String(raw.message_id),
    conversationId: String(raw.conversation_id),
    hierarchyNodeId: String(raw.hierarchy_node_id),
    senderUserId: String(raw.sender_user_id),
    senderName: String(raw.sender_name),
    targetUserId: String(raw.target_user_id),
    mentionText: String(raw.mention_text),
    status: String(raw.status) as MentionStatus,
    createdAt: String(raw.created_at),
    readAt: raw.read_at == null ? null : String(raw.read_at),
    answeredAt: raw.answered_at == null ? null : String(raw.answered_at),
    closedAt: raw.closed_at == null ? null : String(raw.closed_at),
  };
}

export async function loadMentionCandidates(
  query = '',
  hierarchyNodeId?: string,
): Promise<MentionCandidate[]> {
  const rows = await apiGet<Record<string, unknown>[]>('/mentions/candidates', {
    query: { q: query, hierarchy_node_id: hierarchyNodeId },
  });
  return rows.map(normalizeCandidate);
}

export async function loadOnlineUsers(hierarchyNodeId?: string): Promise<MentionCandidate[]> {
  const rows = await apiGet<Record<string, unknown>[]>('/mentions/online', {
    query: { hierarchy_node_id: hierarchyNodeId },
  });
  return rows.map(normalizeCandidate);
}

export async function loadMyMentions(): Promise<UserMention[]> {
  const rows = await apiGet<Record<string, unknown>[]>('/mentions/me');
  return rows.map(normalizeMention);
}

export async function updateMentionStatus(
  mentionId: string,
  status: Exclude<MentionStatus, 'unread'>,
): Promise<UserMention> {
  const row = await apiPatch<Record<string, unknown>, { status: string }>(
    `/mentions/${encodeURIComponent(mentionId)}`,
    { status },
  );
  return normalizeMention(row);
}
