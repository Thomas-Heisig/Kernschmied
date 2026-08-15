import { apiDelete } from './client';

export interface ChatMutationResponse {
  schema_version: '1.0';
  conversation_id: string;
  action: 'delete_message' | 'clear' | 'truncate_after';
  affected_messages: number;
  retained_through_message_id: string | null;
}

export function deleteChatMessage(conversationId: string, messageId: string) {
  return apiDelete<ChatMutationResponse>(
    `/chats/${encodeURIComponent(conversationId)}/messages/${encodeURIComponent(messageId)}`,
  );
}

export function clearChatMessages(conversationId: string) {
  return apiDelete<ChatMutationResponse>(
    `/chats/${encodeURIComponent(conversationId)}/messages`,
  );
}

export function truncateChatMessagesAfter(conversationId: string, messageId: string) {
  return apiDelete<ChatMutationResponse>(
    `/chats/${encodeURIComponent(conversationId)}/messages`,
    { query: { after_message_id: messageId } },
  );
}