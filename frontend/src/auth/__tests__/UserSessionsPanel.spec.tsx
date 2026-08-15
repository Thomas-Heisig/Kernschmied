import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { useAuth } from '../AuthProvider';
import { UserAccountPanelsProvider, useUserPanels } from '../UserAccountPanels';
import { loadSessions } from '../auth-api';

vi.mock('../AuthProvider', () => ({
  useAuth: vi.fn(),
}));

vi.mock('../auth-api', () => ({
  loadSessions: vi.fn(),
  revokeSession: vi.fn(),
  logoutAllSessions: vi.fn(),
}));

function Harness() {
  const panels = useUserPanels();
  return <button onClick={() => panels.openPanel('sessions')}>Sitzungen öffnen</button>;
}

describe('UserSessionsPanel', () => {
  beforeEach(() => {
    vi.resetAllMocks();
    vi.mocked(useAuth).mockReturnValue({
      refreshCurrentUser: vi.fn(),
      markUnauthenticated: vi.fn(),
    } as unknown as ReturnType<typeof useAuth>);
    vi.mocked(loadSessions).mockResolvedValue([
      {
        id: 'current-session',
        authenticationMethod: 'password',
        createdAt: '2026-08-15T12:00:00Z',
        expiresAt: '2026-08-15T20:00:00Z',
        lastSeenAt: null,
        revokedAt: null,
        current: true,
        ipAddress: '127.0.0.1',
        userAgent: 'Mozilla/5.0 Chrome',
      },
    ]);
  });

  it('renders one dialog title, one close action, and the current session', async () => {
    render(
      <UserAccountPanelsProvider>
        <Harness />
      </UserAccountPanelsProvider>,
    );

    fireEvent.click(screen.getByRole('button', { name: 'Sitzungen öffnen' }));

    const dialog = await screen.findByRole('dialog', { name: 'Sitzungen' });
    expect(screen.getByText('Aktuelle Sitzung')).toBeInTheDocument();
    expect(dialog.querySelectorAll('h2')).toHaveLength(1);
    expect(screen.getAllByRole('button', { name: 'Schließen' })).toHaveLength(1);
    expect(screen.queryByText(/interner Fehler/i)).not.toBeInTheDocument();
  });
});