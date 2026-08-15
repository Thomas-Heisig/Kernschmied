import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import RecentNodeSection, { resolveRecentNodes } from '../RecentNodeSection';

const nodes = [
  { id: 'project-a', name: 'Projekt A', type: 'project', children: [] },
  {
    id: 'project-b',
    name: 'Projekt B',
    type: 'project',
    children: [{ id: 'chat-b', name: 'Chat B', type: 'chat', children: [] }],
  },
];

describe('RecentNodeSection', () => {
  beforeEach(() => window.localStorage.clear());

  it('keeps storage order and filters against visible accepted nodes', () => {
    window.localStorage.setItem(
      'kernschmied.sidebar.recent',
      JSON.stringify(['hidden', 'chat-b', 'project-b', 'project-a']),
    );

    expect(resolveRecentNodes(nodes, ['project'])).toEqual([nodes[1], nodes[0]]);
    expect(resolveRecentNodes(nodes, ['chat'], true)).toEqual([nodes[1].children[0]]);
  });

  it('renders navigable recent cards', () => {
    const onNavigate = vi.fn();
    window.localStorage.setItem(
      'kernschmied.sidebar.recent',
      JSON.stringify(['project-b']),
    );

    render(
      <RecentNodeSection
        nodes={nodes}
        acceptedTypes={['project']}
        title="Letzte Projekte"
        description="Zuletzt geöffnet"
        onNavigateToNode={onNavigate}
      />,
    );

    fireEvent.click(screen.getByRole('button', { name: 'Projekt B öffnen' }));
    expect(onNavigate).toHaveBeenCalledWith('project-b');
  });
});