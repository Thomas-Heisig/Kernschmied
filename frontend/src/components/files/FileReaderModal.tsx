import React from 'react';
import Modal from '../ui/Modal';
import type { WorkspaceFile } from '../../contracts/workspace-files';
import { formatFileDate, formatFileSize } from '../../utils/fileUtils';

interface Props {
  file: WorkspaceFile | null;
  isOpen: boolean;
  onClose: () => void;
}

function generateMockPreviewText(file: WorkspaceFile): string {
  return `Vorschau: ${file.name}\nID: ${file.id}\nNode: ${file.nodeId}\nSize: ${formatFileSize(file.size)}\nSource: ${file.source}\n\nDies ist eine generische Vorschau für Mock-Dateien.`;
}

export default function FileReaderModal({ file, isOpen, onClose }: Props) {
  if (!file) return null;

  const isImage = file.mimeType?.startsWith('image/');
  const isText = file.mimeType?.startsWith('text/') || file.name.endsWith('.md') || file.name.endsWith('.txt');

  return (
    <Modal isOpen={isOpen} title={`Vorschau: ${file.name}`} onClose={onClose} confirmLabel="Schließen">
      <div className="space-y-4">
        <div className="text-xs text-text-muted">{file.mimeType} · {formatFileSize(file.size)} · {formatFileDate(file.updatedAt)}</div>

        {isImage && file.previewUrl ? (
          <img src={file.previewUrl} alt={file.name} className="max-h-[60vh] object-contain w-full" />
        ) : isText ? (
          <pre className="max-h-[60vh] overflow-auto whitespace-pre-wrap text-sm font-mono bg-surface p-3 rounded">{generateMockPreviewText(file)}</pre>
        ) : (
          <div className="rounded border border-border p-3 text-sm">Vorschau nicht verfügbar für diesen Dateityp. Metadaten angezeigt oben.</div>
        )}
      </div>
    </Modal>
  );
}
