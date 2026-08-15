import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import RegisterPage from '../RegisterPage';

const register = vi.fn();

vi.mock('../AuthProvider', () => ({
  useAuth: () => ({
    register,
    registrationAvailable: true,
    registrationRequiresInvitation: false,
  }),
}));

describe('RegisterPage', () => {
  it('rejects a short password locally with a clear message', async () => {
    render(<RegisterPage />);

    fireEvent.change(screen.getByLabelText('Benutzername'), {
      target: { value: 'new-user' },
    });
    fireEvent.change(screen.getByLabelText('Anzeigename'), {
      target: { value: 'New User' },
    });
    fireEvent.change(screen.getByLabelText('Passwort', { selector: 'input' }), {
      target: { value: 'short' },
    });
    fireEvent.change(screen.getByLabelText('Passwort bestätigen'), {
      target: { value: 'short' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Registrieren' }));

    expect(
      await screen.findByRole('alert'),
    ).toHaveTextContent('Das Passwort muss mindestens 12 Zeichen lang sein.');
    await waitFor(() => expect(register).not.toHaveBeenCalled());
  });
});