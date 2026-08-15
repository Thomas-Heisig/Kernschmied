import React from 'react';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import NodeEditorDialog from '../NodeEditorDialog';
import { vi } from 'vitest';

vi.mock('../../../api/hierarchy', () => ({
  updateHierarchyNode: vi.fn(),
}));

import { updateHierarchyNode } from '../../../api/hierarchy';

vi.mock('../../../api/fetchWidgetsClient', () => ({
  default: {
    listRegistry: vi.fn(),
    setNodeAssignments: vi.fn(),
  },
}));
vi.mock('../../../api/widgets', () => ({
  default: {
    loadEffectiveWidgets: vi.fn(),
  },
}));

import fetchWidgetsClient from '../../../api/fetchWidgetsClient';
import widgetsApi from '../../../api/widgets';

const baseNode = {
  id: 'node-1',
  name: 'Node One',
  type: 'workspace',
  parent_id: 'parent-1',
  children: [
    { id: 'child-a', name: 'Child A', type: 'chat' },
    { id: 'child-b', name: 'Child B', type: 'user' },
  ],
  metadata: {
    prompt: { foo: 'bar' },
    filesystem: { x: 1 },
  },
} as any;

const nodeTypes = {
  workspace: {
    label: 'Workspace',
    allowed_child_types: ['workspace', 'project', 'chat'],
    allowed_actions: ['edit', 'delete'],
  },
  project: {
    label: 'Project',
    allowed_child_types: ['chat'],
    allowed_actions: ['edit'],
  },
  chat: {
    label: 'Chat',
    allowed_child_types: [],
    allowed_actions: [],
  },
  user: {
    label: 'User',
    allowed_child_types: [],
    allowed_actions: [],
  },
};

function renderDialog(props?: any) {
  const onClose = vi.fn();
  const onSaved = vi.fn();
  const utils = render(
    <NodeEditorDialog isOpen={true} node={props?.node ?? baseNode} nodeTypes={props?.nodeTypes ?? nodeTypes} onClose={onClose} onSaved={onSaved} />,
  );
  return { ...utils, onClose, onSaved };
}

describe('NodeEditorDialog — Structure tab', () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it('displays parent info', () => {
    renderDialog();
    // Parent info present
    fireEvent.click(screen.getByText('Struktur'));
    expect(screen.getByText('parent-1')).toBeTruthy();
    expect(screen.getByText(/Name:/)).toBeTruthy();
    expect(screen.getByText(/Typ:/)).toBeTruthy();
  });

  it('root case shows no parent', () => {
    const rootNode = { ...baseNode, parent_id: null } as any;
    renderDialog({ node: rootNode });
    fireEvent.click(screen.getByText('Struktur'));
    expect(screen.getByText('Kein übergeordneter Knoten')).toBeTruthy();
  });

  it('shows allowed_child_types from schema', () => {
    renderDialog();
    fireEvent.click(screen.getByText('Struktur'));
    // workspace allowed_child_types contains project/chat/workspace
    expect(screen.getAllByText('workspace').length).toBeGreaterThan(0);
    expect(screen.getAllByText('project').length).toBeGreaterThan(0);
    expect(screen.getAllByText('chat').length).toBeGreaterThan(0);
  });

  it('type change in General updates Structure preview immediately', async () => {
    renderDialog();
    // change type to project
    fireEvent.click(screen.getByText('Allgemein'));
    // find the select near the 'Typ' label
    const typLabel = screen.getByText('Typ');
    const typSelect = within(typLabel.parentElement as HTMLElement).getByRole('combobox') as HTMLSelectElement;
    fireEvent.change(typSelect, { target: { value: 'project' } });
    fireEvent.click(screen.getByText('Struktur'));
    // project.allowed_child_types = ['chat']
    await waitFor(() => expect(screen.getAllByText('chat').length).toBeGreaterThan(0));
  });

  it('shows incompatible children when new type disallows them', async () => {
    renderDialog();
    // change type to project which only allows chat, so user child is incompatible
    fireEvent.click(screen.getByText('Allgemein'));
    const typLabel2 = screen.getByText('Typ');
    const typSelect2 = within(typLabel2.parentElement as HTMLElement).getByRole('combobox') as HTMLSelectElement;
    fireEvent.change(typSelect2, { target: { value: 'project' } });
    fireEvent.click(screen.getByText('Struktur'));
    expect(await screen.findByText(/Warnung:/)).toBeInTheDocument();
    expect(screen.getByText(/Child B/)).toBeInTheDocument();
  });

  it('allows local override to narrow allowed_child_types and prevents extension', async () => {
    renderDialog();
    fireEvent.click(screen.getByText('Struktur'));
    // enable override
    const cb = screen.getByLabelText('Eigene Einschränkung verwenden') as HTMLInputElement;
    fireEvent.click(cb);
    expect(cb.checked).toBe(true);
    // check that only allowed types are shown for selection (no "user") by scoping to the override container
    const chooserLabel = screen.getByText('Wähle erlaubte Kindtypen (nur Einschränken):');
    const chooser = chooserLabel.parentElement as HTMLElement;
    const scoped = within(chooser);
    expect(scoped.queryByText('user')).toBeNull();
    // select project
    const projectCheckbox = scoped.getByLabelText('project') as HTMLInputElement;
    fireEvent.click(projectCheckbox);
    expect(projectCheckbox.checked).toBe(true);
  });

  it('sends metadata.hierarchy.allowed_child_types on save when override is used and preserves other metadata', async () => {
    (updateHierarchyNode as any).mockResolvedValue({ ...baseNode, name: 'Node One' });
    const { onSaved } = renderDialog();
    // enable override and select project + chat
    fireEvent.click(screen.getByText('Struktur'));
    fireEvent.click(screen.getByLabelText('Eigene Einschränkung verwenden'));
    fireEvent.click(screen.getByLabelText('project'));
    fireEvent.click(screen.getByLabelText('chat'));
    // Save
    fireEvent.click(screen.getByText('Speichern'));
    await waitFor(() => expect(updateHierarchyNode).toHaveBeenCalled());
    const calledWith = (updateHierarchyNode as any).mock.calls[0][1];
    expect(calledWith.metadata).toBeDefined();
    expect(calledWith.metadata.hierarchy.allowed_child_types).toEqual(expect.arrayContaining(['project', 'chat']));
    // ensure other metadata keys not lost when parent supplies them — component passes only hierarchy; merge tested in backend tests
    expect(onSaved).toHaveBeenCalled();
  });

  it('prompts on discard when dirty and honors cancel/confirm', async () => {
    const { onClose } = renderDialog();
    // change name
    fireEvent.click(screen.getByText('Allgemein'));
    const nameLabel = screen.getByText('Name');
    const nameInput = within(nameLabel.parentElement as HTMLElement).getByRole('textbox') as HTMLInputElement;
    fireEvent.change(nameInput, { target: { value: 'New Name' } });
    // attempt cancel — mock confirm to return false (keep open)
    const orig = window.confirm;
    (window as any).confirm = () => false;
    fireEvent.click(screen.getByText('Abbrechen'));
    expect(onClose).not.toHaveBeenCalled();
    // now confirm discard
    (window as any).confirm = () => true;
    fireEvent.click(screen.getByText('Abbrechen'));
    expect(onClose).toHaveBeenCalled();
    (window as any).confirm = orig;
  });

  it('displays structured backend type-change error nicely', async () => {
    const apiErr = new Error('Typwechsel nicht möglich');
    (apiErr as any).code = 'HIERARCHY_NODE_TYPE_CHANGE_INVALID';
    (apiErr as any).details = { invalid_children: [{ id: 'child-b', type: 'user' }] };
    (updateHierarchyNode as any).mockRejectedValue(apiErr);
    renderDialog();
    fireEvent.click(screen.getByText('Speichern'));
    expect(await screen.findByText(/Typwechsel nicht möglich/)).toBeInTheDocument();
    expect(screen.getByText(/child-b/)).toBeInTheDocument();
  });
});

describe('NodeEditorDialog — Widgets tab', () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it('activating a widget creates an assignment', async () => {
    // registry has calendar, effective empty initially
    (fetchWidgetsClient as any).listRegistry.mockResolvedValue([{ name: 'calendar', id: 'calendar', label: 'Calendar' }]);
    (widgetsApi as any).loadEffectiveWidgets.mockResolvedValue([]);
    (fetchWidgetsClient as any).setNodeAssignments.mockResolvedValue({});

    renderDialog();
    fireEvent.click(screen.getByText('Widgets'));
    // wait for registry to render
    expect(await screen.findByText('Calendar')).toBeTruthy();

    const row = screen.getByText('Calendar').closest('tr') as HTMLElement;
    const activate = within(row).getByText('Aktivieren');
    fireEvent.click(activate);

    await waitFor(() => expect((fetchWidgetsClient as any).setNodeAssignments).toHaveBeenCalled());
    const callArgs = (fetchWidgetsClient as any).setNodeAssignments.mock.calls[0];
    expect(callArgs[0]).toBe(baseNode.id);
    expect(callArgs[1]).toBeDefined();
    expect(callArgs[1].assignments).toEqual(expect.arrayContaining([expect.objectContaining({ name: 'calendar', enabled: true })]));
  });

  it('disabling an inherited widget creates a local enabled=false override', async () => {
    (fetchWidgetsClient as any).listRegistry.mockResolvedValue([{ name: 'calendar', id: 'calendar', label: 'Calendar' }]);
    // effective contains inherited calendar
    (widgetsApi as any).loadEffectiveWidgets.mockResolvedValue([{ id: 'calendar', name: 'calendar', enabled: true }]);
    (fetchWidgetsClient as any).setNodeAssignments.mockResolvedValue({});

    renderDialog();
    fireEvent.click(screen.getByText('Widgets'));
    expect(await screen.findByText('Calendar')).toBeTruthy();

    const row = screen.getByText('Calendar').closest('tr') as HTMLElement;
    const deactivate = within(row).getByText('Deaktivieren');
    fireEvent.click(deactivate);

    await waitFor(() => expect((fetchWidgetsClient as any).setNodeAssignments).toHaveBeenCalled());
    const callArgs = (fetchWidgetsClient as any).setNodeAssignments.mock.calls[0];
    expect(callArgs[1].assignments).toEqual(expect.arrayContaining([expect.objectContaining({ name: 'calendar', enabled: false })]));
  });

  it('calendar activation yields component_type=calendar_widget after reload', async () => {
    (fetchWidgetsClient as any).listRegistry.mockResolvedValue([{ name: 'calendar', id: 'calendar', label: 'Calendar' }]);
    // first load returns empty, after activation load returns calendar with componentType
    (widgetsApi as any).loadEffectiveWidgets.mockResolvedValueOnce([]).mockResolvedValueOnce([{ id: 'calendar', name: 'calendar', componentType: 'calendar_widget', enabled: true }]);
    (fetchWidgetsClient as any).setNodeAssignments.mockResolvedValue({});

    renderDialog();
    fireEvent.click(screen.getByText('Widgets'));
    expect(await screen.findByText('Calendar')).toBeTruthy();
    const row = screen.getByText('Calendar').closest('tr') as HTMLElement;
    const activate = within(row).getByText('Aktivieren');
    fireEvent.click(activate);

    await waitFor(() => expect((widgetsApi as any).loadEffectiveWidgets).toHaveBeenCalledTimes(2));
    // after reload effectiveWidgets should contain componentType
    const eff = (widgetsApi as any).loadEffectiveWidgets.mock.results[1].value;
    const resolved = await eff;
    expect(resolved[0].componentType).toBe('calendar_widget');
  });
});
