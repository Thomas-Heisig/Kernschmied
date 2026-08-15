import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import UserAdministrationPanel from '../UserAdministrationPanel';
import {
  createManagedUser,
  listManagedUsers,
  updateManagedUser,
} from '../auth-api';

vi.mock('../auth-api', () => ({
  createManagedUser: vi.fn(),
  deleteManagedUser: vi.fn(),
  listManagedUsers: vi.fn(),
  resetManagedUserPassword: vi.fn(),
  updateManagedUser: vi.fn(),
}));

const thomas = {
  id: 'user-thomas',
  username: 'thomas',
  displayName: 'Thomas Heisig',
  email: 'thomas@example.test',
  isActive: true,
  isSystem: false,
  accessLevel: 'internal' as const,
  workspaceQuota: null,
  projectQuota: null,
  chatQuota: null,
};

describe('UserAdministrationPanel', () => {
  beforeEach(() => {
    vi.resetAllMocks();
    vi.mocked(listManagedUsers).mockResolvedValue([thomas]);
    vi.mocked(updateManagedUser).mockResolvedValue(thomas);
    vi.mocked(createManagedUser).mockResolvedValue({
      user: { ...thomas, id: 'new-user', username: 'neu' },
      temporaryPassword: 'Temporary-123!',
    });
  });

  it('updates profile data for an existing user', async () => {
    render(<UserAdministrationPanel />);

    fireEvent.click(await screen.findByRole('option', { name: /Thomas Heisig/ }));
    fireEvent.change(screen.getByLabelText('Anzeigename'), {
      target: { value: 'Thomas H.' },
    });
    fireEvent.change(screen.getByLabelText('Bereiche-Kontingent'), {
      target: { value: 'unlimited' },
    });
    fireEvent.change(screen.getByLabelText('Projekte-Kontingent'), {
      target: { value: 'limit' },
    });
    fireEvent.change(screen.getByLabelText('Maximale Projekte'), {
      target: { value: '7' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Speichern' }));

    await waitFor(() => {
      expect(updateManagedUser).toHaveBeenCalledWith('user-thomas', {
        displayName: 'Thomas H.',
        email: 'thomas@example.test',
        isActive: true,
        accessLevel: 'internal',
        workspaceQuota: 'unlimited',
        projectQuota: 7,
        chatQuota: null,
      });
    });
  });

  it('creates a user with a generated temporary password when no password is entered', async () => {
    render(<UserAdministrationPanel />);

    fireEvent.change(screen.getByLabelText('Benutzername'), { target: { value: 'neu' } });
    fireEvent.change(screen.getByLabelText('Anzeigename'), { target: { value: 'Neuer Nutzer' } });
    fireEvent.click(screen.getByRole('button', { name: 'Speichern' }));

    await waitFor(() => {
      expect(createManagedUser).toHaveBeenCalledWith(
        expect.objectContaining({
          username: 'neu',
          displayName: 'Neuer Nutzer',
          generatePassword: true,
          requirePasswordChange: true,
          accessLevel: 'guest',
        }),
      );
    });
    expect(await screen.findByText(/Temporäres Passwort/)).toBeInTheDocument();
  });

  it('rejects a short custom start password before creating the user', async () => {
    render(<UserAdministrationPanel />);

    fireEvent.change(screen.getByLabelText('Benutzername'), { target: { value: 'neu' } });
    fireEvent.change(screen.getByLabelText('Anzeigename'), { target: { value: 'Neuer Nutzer' } });
    fireEvent.change(screen.getByLabelText('Startpasswort (leer = generieren)'), {
      target: { value: 'short' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Speichern' }));

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'Das Startpasswort muss mindestens 12 Zeichen lang sein.',
    );
    expect(createManagedUser).not.toHaveBeenCalled();
  });
});