import { fireEvent, render, screen, within } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import type { HierarchyNode } from '../../../contracts/hierarchy';
import { AppHierarchySidebar } from '../AppHierarchySidebar';

const root: HierarchyNode = {
  id: 'root',
  name: 'System',
  type: 'system',
  actions: [],
  children: [
    {
      id: 'workspace',
      parent_id: 'root',
      name: 'Entwicklung',
      type: 'workspace',
      actions: [],
      children: [
        {
          id: 'project',
          parent_id: 'workspace',
          name: 'Kernschmied UI',
          type: 'project',
          actions: [],
          children: [
            {
              id: 'chat',
              parent_id: 'project',
              name: 'Chat Alpha',
              type: 'chat',
              actions: [],
              children: [],
              metadata: { unread_count: 3 },
            },
          ],
        },
      ],
    },
    {
      id: 'user',
      parent_id: 'root',
      name: 'Thomas',
      type: 'user',
      actions: [],
      children: [],
    },
  ],
};

function renderSidebar() {
  const onSelect = vi.fn();
  const onExpandedNodeIdsChange = vi.fn();
  render(
    <AppHierarchySidebar
      root={root}
      schema={{ node_types: {} } as never}
      selectedNodeId={null}
      expandedNodeIds={new Set(['root', 'workspace', 'project'])}
      onSelect={onSelect}
      onExpandedNodeIdsChange={onExpandedNodeIdsChange}
    />,
  );
  return { onSelect, onExpandedNodeIdsChange };
}

describe('AppHierarchySidebar', () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it('filters the hierarchy by node type while preserving ancestors', () => {
    renderSidebar();

    fireEvent.click(screen.getByRole('button', { name: 'Chats' }));

    expect(screen.getByRole('button', { name: 'Chat Alpha 3' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Entwicklung' })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Thomas' })).not.toBeInTheDocument();
  });

  it('adds selected and starred nodes to quick access', () => {
    const { onSelect } = renderSidebar();

    fireEvent.click(screen.getByRole('button', { name: 'Chat Alpha 3' }));
    expect(onSelect).toHaveBeenCalledWith(expect.objectContaining({ id: 'chat' }));
    expect(within(screen.getByRole('region', { name: 'Zuletzt verwendet' })).getByText('Chat Alpha')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Chat Alpha zu Favoriten hinzufügen' }));
    expect(within(screen.getByRole('region', { name: 'Favoriten' })).getByText('Chat Alpha')).toBeInTheDocument();
    expect(JSON.parse(window.localStorage.getItem('kernschmied.sidebar.favorites') ?? '[]')).toContain('chat');
  });

  it('collapses all expanded nodes from the footer', () => {
    const { onExpandedNodeIdsChange } = renderSidebar();

    fireEvent.click(screen.getByRole('button', { name: 'Alle Knoten einklappen' }));

    expect(onExpandedNodeIdsChange).toHaveBeenCalledWith(new Set());
  });

  it('does not render administrative create actions without callbacks', () => {
    renderSidebar();

    expect(screen.queryByRole('button', { name: 'Neuer Benutzer' })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Neuer Public-Bereich' })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Neuer interner Bereich' })).not.toBeInTheDocument();
  });
});