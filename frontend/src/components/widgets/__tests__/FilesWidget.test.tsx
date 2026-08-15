import { render, screen, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import FilesWidget from '../FilesWidget';

describe('FilesWidget', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('loads files for the selected hierarchy node', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify({ items: [] }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    );

    render(<FilesWidget widget={{ id: 'files' }} nodeId="user-admin" />);

    expect(await screen.findByText('Keine Dateien gefunden.')).toBeInTheDocument();
    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        '/api/v1/files?node_id=user-admin',
        { credentials: 'include' },
      );
    });
  });
});
