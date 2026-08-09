export interface WorkspaceFile {
  id: string;
  nodeId: string;
  ownerId?: string;

  name: string;
  description?: string;

  size: number;
  mimeType: string;

  createdAt: string;
  updatedAt: string;

  previewUrl?: string;
  downloadUrl?: string;

  source: 'mock' | 'uploaded' | 'generated' | 'projection';

  inherited?: boolean;
  inheritedFromNodeId?: string;
  inheritedFromNodeName?: string;
}

export interface FilesListResponse {
  schemaVersion: string;
  nodeId: string;
  items: WorkspaceFile[];
  requestId?: string;
}
