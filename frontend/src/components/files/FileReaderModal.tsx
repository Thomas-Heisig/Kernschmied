// F:\Kernschmied\frontend\src\components\files\FileReaderModal.tsx

import Modal from '../ui/Modal';
import type { WorkspaceFile } from '../../contracts/workspace-files';
import { formatFileDate, formatFileSize } from '../../utils/fileUtils';
import IconBadge from '../common/IconBadge';
import { FileText, FileImage, File } from 'lucide-react';

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
  const isText =
    file.mimeType?.startsWith('text/') ||
    file.name.endsWith('.md') ||
    file.name.endsWith('.txt') ||
    file.name.endsWith('.json') ||
    file.name.endsWith('.csv');

  return (
    <Modal isOpen={isOpen} title={`Vorschau: ${file.name}`} onClose={onClose} confirmLabel="Schließen">
      <div className="space-y-4">
        {/* Metadaten-Zeile */}
        <div className="flex flex-wrap items-center gap-3 text-xs text-text-muted dark:text-gray-500">
          <div className="flex items-center gap-1.5">
            <IconBadge
              icon={
                isImage ? (
                  <FileImage />
                ) : isText ? (
                  <FileText />
                ) : (
                  <File />
                )
              }
              size="sm"
              variant="default"
            />
            <span>{file.mimeType || 'unbekannt'}</span>
          </div>
          <span>·</span>
          <span>{formatFileSize(file.size)}</span>
          <span>·</span>
          <span>{formatFileDate(file.updatedAt)}</span>
        </div>

        {/* Inhalt */}
        <div className="min-h-50 rounded-xl border border-border-soft bg-white/50 dark:border-white/10 dark:bg-slate-900/30">
          {isImage && file.previewUrl ? (
            <img
              src={file.previewUrl}
              alt={file.name}
              className="max-h-[60vh] w-full rounded-xl object-contain"
            />
          ) : isText ? (
            <pre className="max-h-[60vh] overflow-auto whitespace-pre-wrap rounded-xl p-4 text-sm font-mono text-text-soft dark:text-gray-300">
              {generateMockPreviewText(file)}
            </pre>
          ) : (
            <div className="flex h-50 flex-col items-center justify-center gap-2 text-sm text-text-muted dark:text-gray-500">
              <IconBadge icon={<File />} size="lg" variant="default" />
              <p>Vorschau nicht verfügbar für diesen Dateityp.</p>
              <p className="text-xs">Metadaten werden oben angezeigt.</p>
            </div>
          )}
        </div>
      </div>
    </Modal>
  );
}