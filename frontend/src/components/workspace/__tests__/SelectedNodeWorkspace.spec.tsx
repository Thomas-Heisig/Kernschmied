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

    render(
      <SelectedNodeWorkspace
        node={{
          id: 'user-guest-user',
          type: 'user',
          name: 'Thomas',
          metadata: { entity_type: 'user', entity_id: 'guest-user' },
          actions: ['read', 'create_child'],
          children: [
            {
              id: 'workspace-thomas',
              type: 'workspace',
              name: 'Mein Arbeitsbereich',
              actions: ['read'],
              children: [],
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

    fireEvent.click(screen.getByRole('button', { name: 'Bereich erstellen' }));
    expect(onAction).toHaveBeenCalledWith(
      'create_child',
      expect.objectContaining({ id: 'user-guest-user' }),
    );

    fireEvent.click(screen.getByRole('button', { name: /Einstellungen/ }));
    expect(openPanel).toHaveBeenCalledWith('settings');

    fireEvent.click(screen.getByRole('button', { name: /Mein Arbeitsbereich/ }));
    expect(onNavigateToNode).toHaveBeenCalledWith('workspace-thomas');
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
    const { rerender } = render(
      <SelectedNodeWorkspace
        node={{
          id: 'workspace-1',
          type: 'workspace',
          name: 'Bereich 1',
          actions: ['read', 'create_child'],
          children: [],
        }}
        onAction={onAction}
      />,
    );

    fireEvent.click(screen.getByRole('button', { name: 'Projekt erstellen' }));
    fireEvent.click(screen.getByRole('button', { name: 'Chat erstellen' }));
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
          children: [],
        }}
        onAction={onAction}
      />,
    );

    fireEvent.click(screen.getByRole('button', { name: 'Chat erstellen' }));
    expect(onAction).toHaveBeenLastCalledWith(
      'create_child',
      expect.objectContaining({ id: 'project-1' }),
    );
  });
});
