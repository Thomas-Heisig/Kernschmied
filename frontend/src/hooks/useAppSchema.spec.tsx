import { renderHook, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { apiGet } from '../api/client';
import type { HierarchyTree } from '../contracts/hierarchy';
import type { UISchema } from '../contracts/schema';
import type { AppBootstrap } from '../types/bootstrap';
import { useAppSchema } from './useAppSchema';

vi.mock('../api/client', async (importOriginal) => ({
  ...(await importOriginal<typeof import('../api/client')>()),
  apiGet: vi.fn(),
}));

const schema: UISchema = {
  schema_name: 'test',
  schema_version: '1.0',
  node_types: {},
  forms: {},
  components: {},
  actions: {},
  metadata: {},
};

function tree(id: string, name: string): HierarchyTree {
  return {
    schema_version: '1.0',
    revision: 1,
    root: {
      id,
      type: 'user',
      name,
      parent_id: null,
      actions: ['read'],
      children: [],
      metadata: {},
    },
  };
}

const bootstrap: AppBootstrap = {
  security: {
    profile: 'development',
    authenticationRequired: false,
    developmentIdentityActive: true,
    availableLoginMethods: [],
  },
  features: { developmentAdminLogin: true },
  endpoints: {
    uiSchema: '/api/v1/ui/schema',
    hierarchy: '/api/v1/hierarchy',
  },
};

describe('useAppSchema', () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it('discards the previous hierarchy on logout and reloads it for the next user', async () => {
    const adminTree = tree('system-root', 'System Root');
    const guestTree = tree('user-thomas', 'Thomas-Heisig');
    let hierarchyRequests = 0;

    vi.mocked(apiGet).mockImplementation(async (endpoint) => {
      if (endpoint === '/api/v1/ui/schema') return schema;
      if (endpoint === '/api/v1/hierarchy') {
        hierarchyRequests += 1;
        return hierarchyRequests === 1 ? adminTree : guestTree;
      }
      throw new Error(`Unexpected endpoint: ${endpoint}`);
    });

    const { result, rerender } = renderHook(
      ({ enabled, identityKey }) => useAppSchema(enabled, bootstrap, identityKey),
      { initialProps: { enabled: true, identityKey: 'admin' } },
    );

    await waitFor(() => expect(result.current.hierarchy?.id).toBe('system-root'));

    rerender({ enabled: false, identityKey: null });
    await waitFor(() => expect(result.current.hierarchy).toBeNull());

    rerender({ enabled: true, identityKey: 'thomas' });
    await waitFor(() => expect(result.current.hierarchy?.id).toBe('user-thomas'));
    expect(hierarchyRequests).toBe(2);
  });
});