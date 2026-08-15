import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { useAuth } from '../../../auth/AuthProvider';
import { useUserPanels } from '../../../auth/UserAccountPanels';
import { loadOwnHierarchyQuotas } from '../../../api/hierarchy';
import { SelectedNodeWorkspace } from '../SelectedNodeWorkspace';

vi.mock('../../../auth/AuthProvider', () => ({
  useAuth: vi.fn(),
}));

vi.mock('../../../auth/UserAccountPanels', () => ({
  useUserPanels: vi.fn(),
}));

vi.mock('../../../api/hierarchy', () => ({
  loadOwnHierarchyQuotas: vi.fn(),
}));

vi.mock('../../widgets/WidgetBadges', () => ({
  default: () => null,
}));

vi.mock('../../widgets/WidgetsForNode', () => ({
  default: () => <div>Persönliche Widget-Inhalte</div>,
}));

const openPanel = vi.fn();

const guestUser = {
  id: 'guest-user',
  username: 'Thomas-Heisig',
  displayName: 'Thomas',
  email: 'thomas@example.test',
  tenant: null,
  roles: ['guest'],
  authenticated: true,
  developmentSession: false,
  passwordLoginAvailable: true,
  createdAt: null,
  lastLoginAt: null,
  schemaVersion: '1.0',
};

describe('SelectedNodeWorkspace user area', () => {
  beforeEach(() => {
    vi.resetAllMocks();
    window.localStorage.clear();
    vi.mocked(useAuth).mockReturnValue({ user: guestUser } as ReturnType<typeof useAuth>);
    vi.mocked(useUserPanels).mockReturnValue({
      activePanel: null,
      openPanel,
      closePanel: vi.fn(),
    });
    vi.mocked(loadOwnHierarchyQuotas).mockResolvedValue({
      accessLevel: 'guest',
      limits: { workspace: 1, project: 2, chat: 5 },
      usage: { workspace: 0, project: 0, chat: 0 },
      remaining: { workspace: 1, project: 2, chat: 5 },
    });
  });

  it('renders the own user area without technical schema or prompt details', async () => {
    const onNavigateToNode = vi.fn();
    const onAction = vi.fn();
    window.localStorage.setItem('kernschmied.sidebar.recent', JSON.stringify(['chat-planung']));

    render(
      <SelectedNodeWorkspace
        node={{
          id: 'user-guest-user',
          type: 'user',
          name: 'Thomas',
          metadata: { entity_type: 'user', entity_id: 'guest-user' },
          actions: ['read', 'create_child', 'edit_prompt'],
          children: [
            {
              id: 'workspace-thomas',
              type: 'workspace',
              name: 'Mein Arbeitsbereich',
              actions: ['read'],
              children: [
                {
                  id: 'project-website',
                  type: 'project',
                  name: 'Website Relaunch',
                  actions: ['read'],
                  children: [
                    {
                      id: 'chat-planung',
                      type: 'chat',
                      name: 'Planungsrunde',
                      actions: ['read'],
                      children: [],
                    },
                  ],
                },
              ],
            },
          ],
        }}
        schema={{
          node_types: {
            user: {
              label: 'Benutzer',
              allowed_actions: ['rename', 'create_child'],
              allowed_child_types: ['workspace'],
              system_prompt: 'Technischer Basisprompt',
            },
          },
        }}
        onNavigateToNode={onNavigateToNode}
        onAction={onAction}
      />,
    );

    expect(screen.getByRole('heading', { name: 'Mein Bereich: Thomas' })).toBeInTheDocument();
    expect(screen.getByText('Thomas-Heisig')).toBeInTheDocument();
    expect(screen.getByText('Gast')).toBeInTheDocument();
    expect(screen.queryByText('Erlaubte Aktionen')).not.toBeInTheDocument();
    expect(screen.queryByText('Rohdefinition')).not.toBeInTheDocument();
    expect(screen.queryByText('Technischer Basisprompt')).not.toBeInTheDocument();
    expect(await screen.findByText('0/1')).toBeInTheDocument();
    expect(screen.getByText('0/2')).toBeInTheDocument();
    expect(screen.getByText('0/5')).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Verfügbare Projekte' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Website Relaunch öffnen' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Letzte Chats' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Planungsrunde öffnen' })).toBeInTheDocument();
    expect(screen.getByText('Widgets & Anbindungen')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Bereich erstellen' }));
    expect(onAction).toHaveBeenCalledWith(
      'create_child',
      expect.objectContaining({ id: 'user-guest-user' }),
    );

    fireEvent.click(screen.getByRole('button', { name: 'Prompt bearbeiten' }));
    expect(onAction).toHaveBeenCalledWith(
      'edit_prompt',
      expect.objectContaining({ id: 'user-guest-user' }),
    );

    fireEvent.click(screen.getByRole('button', { name: /Einstellungen/ }));
    expect(openPanel).toHaveBeenCalledWith('settings');

    fireEvent.click(screen.getByRole('button', { name: /Mein Arbeitsbereich/ }));
    expect(onNavigateToNode).toHaveBeenCalledWith('workspace-thomas');

    fireEvent.click(screen.getByRole('button', { name: 'Website Relaunch öffnen' }));
    expect(onNavigateToNode).toHaveBeenCalledWith('project-website');

    fireEvent.click(screen.getByRole('button', { name: 'Planungsrunde öffnen' }));
    expect(onNavigateToNode).toHaveBeenCalledWith('chat-planung');
  });

  it('does not expose the signed-in administrators profile in another user area', () => {
    vi.mocked(useAuth).mockReturnValue({
      user: {
        ...guestUser,
        id: 'admin-user',
        username: 'admin',
        displayName: 'Administrator',
        email: 'admin@example.test',
        roles: ['admin'],
      },
    } as ReturnType<typeof useAuth>);

    render(
      <SelectedNodeWorkspace
        node={{
          id: 'user-guest-user',
          type: 'user',
          name: 'Thomas',
          metadata: { entity_type: 'user', entity_id: 'guest-user' },
          children: [],
        }}
      />,
    );

    expect(screen.getByRole('heading', { name: 'Benutzerbereich: Thomas' })).toBeInTheDocument();
    expect(screen.queryByText('admin@example.test')).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Persönliche Einstellungen' })).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Benutzer verwalten' }));
    expect(openPanel).toHaveBeenCalledWith('users');
  });

  it('wires project and chat creation to effective node actions', () => {
    const onAction = vi.fn();
    const onNavigateToNode = vi.fn();
    window.localStorage.setItem(
      'kernschmied.sidebar.recent',
      JSON.stringify(['chat-recent', 'project-recent']),
    );
    const { rerender } = render(
      <SelectedNodeWorkspace
        node={{
          id: 'workspace-1',
          type: 'workspace',
          name: 'Bereich 1',
          actions: ['read', 'create_child'],
          children: [
            {
              id: 'project-recent',
              type: 'project',
              name: 'Letztes Projekt',
              actions: ['read'],
              children: [],
            },
          ],
        }}
        onAction={onAction}
        onNavigateToNode={onNavigateToNode}
      />,
    );

    fireEvent.click(screen.getByRole('button', { name: 'Projekt erstellen' }));
    fireEvent.click(screen.getByRole('button', { name: 'Chat erstellen' }));
    expect(
      screen
        .getByText('Gemeinsamer Rahmen für Projekte, direkte Chats, Zugriffsregeln und Bereichsfunktionen.')
        .closest('section'),
    ).toHaveAttribute('aria-label', 'Bereich: Bereich 1');
    expect(screen.getByRole('heading', { name: 'Letzte Projekte' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Projekte im Bereich' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Direkte Chats' })).toBeInTheDocument();
    const projectButtons = screen.getAllByRole('button', { name: 'Letztes Projekt öffnen' });
    expect(projectButtons).toHaveLength(2);
    fireEvent.click(projectButtons[1]);
    expect(onNavigateToNode).toHaveBeenCalledWith('project-recent');
    expect(onAction).toHaveBeenNthCalledWith(
      1,
      'create_child',
      expect.objectContaining({ id: 'workspace-1' }),
    );
    expect(onAction).toHaveBeenNthCalledWith(
      2,
      'create_chat',
      expect.objectContaining({ id: 'workspace-1' }),
    );

    rerender(
      <SelectedNodeWorkspace
        node={{
          id: 'project-1',
          type: 'project',
          name: 'Projekt 1',
          actions: ['read', 'create_child'],
          children: [
            {
              id: 'chat-recent',
              type: 'chat',
              name: 'Letzter Chat',
              actions: ['read'],
              children: [],
            },
          ],
        }}
        onAction={onAction}
        onNavigateToNode={onNavigateToNode}
      />,
    );

    fireEvent.click(screen.getByRole('button', { name: 'Chat erstellen' }));
    expect(
      screen
        .getByText('Arbeitskontext für Chats, Projektprompt, Metadaten und angebundene Werkzeuge.')
        .closest('section'),
    ).toHaveAttribute('aria-label', 'Projekt: Projekt 1');
    expect(screen.getByRole('button', { name: 'Projektprompt' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Projektwidgets' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Letzte Chats' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Chats im Projekt' })).toBeInTheDocument();
    const chatButtons = screen.getAllByRole('button', { name: 'Letzter Chat öffnen' });
    expect(chatButtons).toHaveLength(2);
    fireEvent.click(chatButtons[1]);
    expect(onNavigateToNode).toHaveBeenCalledWith('chat-recent');
    expect(onAction).toHaveBeenLastCalledWith(
      'create_child',
      expect.objectContaining({ id: 'project-1' }),
    );
  });

  it('uses the shared node overview for the system root', () => {
    render(
      <SelectedNodeWorkspace
        node={{
          id: 'system-root',
          type: 'system',
          name: 'System Root',
          children: [],
        }}
      />,
    );

    expect(
      screen
        .getByText('Zentrale Betriebsübersicht, Konfiguration, Prompt und registrierte Systemfunktionen.')
        .closest('section'),
    ).toHaveAttribute('aria-label', 'Systemknoten: System Root');
  });
});
