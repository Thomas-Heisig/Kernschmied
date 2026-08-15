import { beforeEach, describe, expect, it, vi } from 'vitest';

import { apiGet } from '../../api/client';
import { loadCurrentUser } from '../auth-api';

vi.mock('../../api/client', () => ({
  apiGet: vi.fn(),
  apiPost: vi.fn(),
  apiPatch: vi.fn(),
  apiDelete: vi.fn(),
}));

describe('loadCurrentUser', () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it('keeps a nullable email null and preserves distinct profile names', async () => {
    vi.mocked(apiGet).mockResolvedValue({
      id: 'guest-user',
      username: 'ui-area-check',
      display_name: 'UI Bereich Check',
      email: null,
      authenticated: true,
      roles: ['guest'],
    });

    const result = await loadCurrentUser('/api/v1/auth/me');

    expect(result.authenticated).toBe(true);
    expect(result.user).toMatchObject({
      username: 'ui-area-check',
      displayName: 'UI Bereich Check',
      email: null,
    });
  });
});