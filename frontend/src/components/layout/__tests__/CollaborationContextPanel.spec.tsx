import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import CollaborationContextPanel from '../CollaborationContextPanel';
import {
  loadOnlineUsers,
} from '../../../api/mentions';
import { loadMailboxMessages, loadMyMailbox, updateMailboxMessage } from '../../../api/mailbox';

vi.mock('../../../api/mentions', () => ({
  loadOnlineUsers: vi.fn(),
}));

vi.mock('../../../api/mailbox', () => ({
  loadMailboxMessages: vi.fn(),
  loadMyMailbox: vi.fn(),
  updateMailboxMessage: vi.fn(),
}));

const onlineUser = {
  userId: 'michael-id',
  username: 'michael',
  displayName: 'Michael Beispiel',
  online: true,
};

const mailbox = {
  id: 'mailbox-1',
  userId: 'michael-id',
  internalAddress: 'michael-id@users.kernschmied.local',
  externalEmail: null,
  emailDeliveryEnabled: false,
  emailProvider: null,
  emailReady: false,
};

const message = {
  id: 'mailbox-message-1',
  mailboxId: 'mailbox-1',
  senderUserId: 'thomas-id',
  senderName: 'Thomas',
  relatedMentionId: 'mention-1',
  hierarchyNodeId: 'chat-1',
  subject: 'Neue Benutzeranfrage',
  body: '@michael Bitte den Termin prüfen.',
  messageType: 'mention',
  status: 'unread' as const,
  channel: 'internal' as const,
  deliveryStatus: 'delivered',
  emailTo: null,
  createdAt: '2026-08-15T16:00:00Z',
  readAt: null,
  archivedAt: null,
};

describe('CollaborationContextPanel', () => {
  beforeEach(() => {
    vi.mocked(loadOnlineUsers).mockResolvedValue([onlineUser]);
    vi.mocked(loadMyMailbox).mockResolvedValue(mailbox);
    vi.mocked(loadMailboxMessages).mockResolvedValue([message]);
    vi.mocked(updateMailboxMessage).mockImplementation(async (_id, status) => ({
      ...message,
      status,
    }));
  });

  it('shows online users and lets the recipient complete a request', async () => {
    render(<CollaborationContextPanel hierarchyNodeId="chat-1" />);

    expect(await screen.findByText('Michael Beispiel')).toBeInTheDocument();
    expect(screen.getByText('michael-id@users.kernschmied.local')).toBeInTheDocument();
    expect(screen.getByText('E-Mail vorbereitet, noch nicht aktiviert')).toBeInTheDocument();
    expect(screen.getByText('@michael Bitte den Termin prüfen.')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /Archivieren/ }));

    await waitFor(() => {
      expect(updateMailboxMessage).toHaveBeenCalledWith('mailbox-message-1', 'archived');
    });
    expect(screen.queryByText('@michael Bitte den Termin prüfen.')).not.toBeInTheDocument();
    expect(loadOnlineUsers).toHaveBeenCalledWith('chat-1');
  });
});
