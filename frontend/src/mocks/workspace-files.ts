import type { WorkspaceFile } from "../contracts/workspace-files";
import type { HierarchyNode } from "../contracts/hierarchy";

function isoNow(): string {
  return new Date().toISOString();
}

export function createMockWorkspaceFilesForNode(node: HierarchyNode): WorkspaceFile[] {
  const baseName = node.name.replace(/\s+/g, "_");
  const idPrefix = `mock:${node.id}`;
  const now = isoNow();

  const files: WorkspaceFile[] = [];

  // Helper to push deterministic entries
  function push(type: string, idx: number, name: string, size: number, mime: string) {
    files.push({
      id: `${idPrefix}:${type}:${idx}`,
      nodeId: node.id,
      ownerId: node.metadata && (node.metadata.owner_id as string) ? (node.metadata!.owner_id as string) : undefined,
      name,
      description: undefined,
      size,
      mimeType: mime,
      createdAt: now,
      updatedAt: now,
      previewUrl: undefined,
      downloadUrl: undefined,
      source: 'mock',
    });
  }

  switch (node.type) {
    case 'user':
    case 'person':
      push('profile', 1, `${baseName}_profil.jpg`, 43221, 'image/jpeg');
      push('notes', 1, `${baseName}_notizen.txt`, 1023, 'text/plain');
      break;

    case 'workspace':
    case 'area':
    case 'bereich':
      push('doc', 1, `${baseName}_bereichsdokumentation.pdf`, 245760, 'application/pdf');
      push('contacts', 1, `${baseName}_kontakte.xlsx`, 65234, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet');
      push('notes', 1, `${baseName}_notizen.txt`, 2048, 'text/plain');
      break;

    case 'project':
      push('proposal', 1, `${baseName}_projektbeschreibung.pdf`, 198765, 'application/pdf');
      push('materials', 1, `${baseName}_materialliste.xlsx`, 54233, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet');
      push('schedule', 1, `${baseName}_terminplan.csv`, 1234, 'text/csv');
      break;

    case 'chat':
      push('notes', 1, `${baseName}_chat_notizen.txt`, 2048, 'text/plain');
      push('summary', 1, `${baseName}_zusammenfassung.md`, 4096, 'text/markdown');
      break;

    case 'folder':
    default:
      // generic small set
      push('readme', 1, `${baseName}_readme.txt`, 512, 'text/plain');
      break;
  }

  return files;
}

export const MOCK_WORKSPACE_FILES_BY_NODE: Record<string, WorkspaceFile[]> = {};
