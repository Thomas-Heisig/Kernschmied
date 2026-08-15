import { apiDelete, apiGet, apiPatch } from './client';

export interface UserMailbox {
  id: string;
  userId: string;
  internalAddress: string;
  externalEmail: string | null;
  emailDeliveryEnabled: boolean;
  emailProvider: string | null;
  emailReady: boolean;
}

export type MailboxMessageStatus = 'unread' | 'read' | 'archived';

export interface MailboxMessage {
  id: string;
  mailboxId: string;
  senderUserId: string | null;
  senderName: string | null;
  relatedMentionId: string | null;
  hierarchyNodeId: string | null;
  subject: string;
  body: string;
  messageType: string;
  status: MailboxMessageStatus;
  channel: 'internal' | 'email';
  deliveryStatus: string;
  emailTo: string | null;
  createdAt: string;
  readAt: string | null;
  archivedAt: string | null;
}

function normalizeMailbox(raw: Record<string, unknown>): UserMailbox {
  return {
    id: String(raw.id),
    userId: String(raw.user_id),
    internalAddress: String(raw.internal_address),
    externalEmail: raw.external_email == null ? null : String(raw.external_email),
    emailDeliveryEnabled: Boolean(raw.email_delivery_enabled),
    emailProvider: raw.email_provider == null ? null : String(raw.email_provider),
    emailReady: Boolean(raw.email_ready),
  };
}

function normalizeMessage(raw: Record<string, unknown>): MailboxMessage {
  return {
    id: String(raw.id),
    mailboxId: String(raw.mailbox_id),
    senderUserId: raw.sender_user_id == null ? null : String(raw.sender_user_id),
    senderName: raw.sender_name == null ? null : String(raw.sender_name),
    relatedMentionId: raw.related_mention_id == null ? null : String(raw.related_mention_id),
    hierarchyNodeId: raw.hierarchy_node_id == null ? null : String(raw.hierarchy_node_id),
    subject: String(raw.subject),
    body: String(raw.body),
    messageType: String(raw.message_type),
    status: String(raw.status) as MailboxMessageStatus,
    channel: String(raw.channel) as 'internal' | 'email',
    deliveryStatus: String(raw.delivery_status),
    emailTo: raw.email_to == null ? null : String(raw.email_to),
    createdAt: String(raw.created_at),
    readAt: raw.read_at == null ? null : String(raw.read_at),
    archivedAt: raw.archived_at == null ? null : String(raw.archived_at),
  };
}

export async function loadMyMailbox(): Promise<UserMailbox> {
  return normalizeMailbox(await apiGet<Record<string, unknown>>('/mailbox/me'));
}

export async function loadMailboxMessages(): Promise<MailboxMessage[]> {
  const rows = await apiGet<Record<string, unknown>[]>('/mailbox/messages');
  return rows.map(normalizeMessage);
}

export async function updateMailboxMessage(
  messageId: string,
  status: Exclude<MailboxMessageStatus, 'unread'>,
): Promise<MailboxMessage> {
  const row = await apiPatch<Record<string, unknown>, { status: string }>(
    `/mailbox/messages/${encodeURIComponent(messageId)}`,
    { status },
  );
  return normalizeMessage(row);
}

export async function deleteMailboxMessage(messageId: string): Promise<void> {
  await apiDelete(`/mailbox/messages/${encodeURIComponent(messageId)}`);
}