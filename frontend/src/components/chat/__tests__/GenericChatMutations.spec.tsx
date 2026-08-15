import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { GenericChatView } from '../GenericChatView';

const mocks = vi.hoisted(() => ({
  clearChatMessages: vi.fn(),
  deleteChatMessage: vi.fn(),
  fetchHistory: vi.fn(),
  truncateChatMessagesAfter: vi.fn(),
}));

const appState = {
  hierarchyTree: null,
  selectedNodeId: 'chat-node',
};

vi.mock('../../../api/chats', () => ({
  clearChatMessages: mocks.clearChatMessages,
  deleteChatMessage: mocks.deleteChatMessage,
  truncateChatMessagesAfter: mocks.truncateChatMessagesAfter,
}));

vi.mock('../../../store', () => ({
  useAppStoreState: () => appState,
  selectSelectedNode: () => ({
    id: 'chat-node',
    metadata: { entity_type: 'conversation', entity_id: 'conversation-1' },
  }),
}));

vi.mock('../../../hooks/useChatHistory', () => ({
  useChatHistory: () => ({
    fetchHistory: mocks.fetchHistory,
    loading: false,
    error: null,
    messages: null,
  }),
}));

vi.mock('../../../auth/auth-api', () => ({
  loadUserPreferences: vi.fn().mockResolvedValue(null),
}));

vi.mock('../../../api/mentions', () => ({
  loadMentionCandidates: vi.fn().mockResolvedValue([]),
}));

vi.mock('../../../hooks/useEffectiveWidgets', () => ({
  default: () => ({ widgets: [], isLoading: false }),
}));

vi.mock('../../layout/WorkspaceLayout', () => ({
  default: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

const history = [
  {
    id: 'message-1',
    role: 'user',
    content: 'Erste Nachricht',
    created_at: '2026-08-15T10:00:00Z',
    status: 'complete',
    parent_message_id: null,
    ui_context: {},
  },
  {
    id: 'message-2',
    role: 'assistant',
    content: 'Zweite Nachricht',
    created_at: '2026-08-15T10:01:00Z',
    status: 'complete',
    parent_message_id: null,
    ui_context: {},
  },
];

function renderChat(onNavigateToNode = vi.fn(), canManageHistory = true) {
  return {
    onNavigateToNode,
    ...render(
      <GenericChatView
        title="Testchat"
        hierarchyNodeId="chat-node"
        hierarchyNodeType="chat"
        childNodes={[
          {
            id: 'child-chat',
            type: 'chat',
            name: 'Unterchat A',
            children: [],
          },
        ]}
        onNavigateToNode={onNavigateToNode}
        canManageHistory={canManageHistory}
      />,
    ),
  };
}

describe('GenericChatView history mutations', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    window.localStorage.clear();
    window.localStorage.setItem(
      'kernschmied.sidebar.recent',
      JSON.stringify(['child-chat']),
    );
    mocks.fetchHistory.mockResolvedValue(history);
    mocks.clearChatMessages.mockResolvedValue({ affected_messages: 2 });
    mocks.deleteChatMessage.mockResolvedValue({ affected_messages: 1 });
    mocks.truncateChatMessagesAfter.mockResolvedValue({ affected_messages: 1 });
    vi.spyOn(window, 'confirm').mockReturnValue(true);
    Element.prototype.scrollIntoView = vi.fn();
  });

  it('shows recent subchats and clears the complete history', async () => {
    const { onNavigateToNode } = renderChat();

    expect(await screen.findByText('Erste Nachricht')).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Letzte Unterchats' })).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Unterchat A öffnen' }));
    expect(onNavigateToNode).toHaveBeenCalledWith('child-chat');

    fireEvent.click(screen.getByRole('button', { name: 'Chat bereinigen' }));
    await waitFor(() => {
      expect(mocks.clearChatMessages).toHaveBeenCalledWith('conversation-1');
    });
    expect(screen.getByText('Noch keine Nachrichten')).toBeInTheDocument();
  });

  it('deletes one persisted message', async () => {
    renderChat();
    expect(await screen.findByText('Erste Nachricht')).toBeInTheDocument();

    fireEvent.click(screen.getAllByRole('button', { name: 'Nachricht löschen' })[0]);
    await waitFor(() => {
      expect(mocks.deleteChatMessage).toHaveBeenCalledWith(
        'conversation-1',
        'message-1',
      );
    });
    expect(screen.queryByText('Erste Nachricht')).not.toBeInTheDocument();
    expect(screen.getByText('Zweite Nachricht')).toBeInTheDocument();
  });

  it('truncates later messages and resumes after the selected point', async () => {
    renderChat();
    expect(await screen.findByText('Zweite Nachricht')).toBeInTheDocument();

    fireEvent.click(
      screen.getAllByRole('button', { name: 'Chat ab dieser Nachricht fortsetzen' })[0],
    );
    await waitFor(() => {
      expect(mocks.truncateChatMessagesAfter).toHaveBeenCalledWith(
        'conversation-1',
        'message-1',
      );
    });
    expect(screen.getByText('Erste Nachricht')).toBeInTheDocument();
    expect(screen.queryByText('Zweite Nachricht')).not.toBeInTheDocument();
  });

  it('hides destructive history controls without delete permission', async () => {
    renderChat(vi.fn(), false);
    expect(await screen.findByText('Erste Nachricht')).toBeInTheDocument();

    expect(screen.queryByRole('button', { name: 'Chat bereinigen' })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Nachricht löschen' })).not.toBeInTheDocument();
    expect(
      screen.queryByRole('button', { name: 'Chat ab dieser Nachricht fortsetzen' }),
    ).not.toBeInTheDocument();
  });
});
