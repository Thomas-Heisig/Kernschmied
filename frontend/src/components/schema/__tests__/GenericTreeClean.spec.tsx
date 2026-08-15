import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import type { HierarchyNode } from '../../../contracts/hierarchy';
import { GenericTree } from '../GenericTreeClean';

describe('GenericTree permission actions', () => {
  it('does not show a command menu for a read-only node', () => {
    const root: HierarchyNode = {
      id: 'user-bob',
      type: 'user',
      name: 'Bob',
      actions: ['read'],
      children: [],
    };

    render(
      <GenericTree
        root={root}
        schema={{ node_types: {} } as never}
        onSelect={vi.fn()}
      />,
    );

    expect(screen.queryByRole('button', { name: 'Weitere Aktionen' })).not.toBeInTheDocument();
  });
});