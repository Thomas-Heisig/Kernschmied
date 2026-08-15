// F:\Kernschmied\frontend\src\components\files\WorkspaceFilesSection.tsx

import React, { useState } from 'react';
import { RefreshCw, Upload, FolderOpen } from 'lucide-react';
import IconBadge from '../common/IconBadge';
import WorkspaceFileIcon from './WorkspaceFileIcon';
import FileReaderModal from './FileReaderModal';
import { formatFileDate, formatFileSize } from '../../utils/fileUtils';
import { useWorkspaceFiles } from '../../hooks/useWorkspaceFiles';

import type { WorkspaceFile } from '../../contracts/workspace-files';

interface SelectedNodeLite {
  id: string;
  name: string;
  type?: string;
  metadata?: Record<string, unknown> | null;
}

interface Props {
  selectedNode?: SelectedNodeLite | null;
  maxVisible?: number;
  includeInherited?: boolean;
  onOpenFile?: (file: WorkspaceFile) => void;
  onDownloadFile?: (file: WorkspaceFile) => void;
  onUploadRequested?: (nodeId: string) => void;
}

export default function WorkspaceFilesSection({
  selectedNode,
  maxVisible = 5,
  includeInherited = false,
  onOpenFile,
  onDownloadFile,
  onUploadRequested,
}: Props) {
  const { files, isLoading, error, reload } = useWorkspaceFiles({
    node: (selectedNode as any) ?? null,
    includeInherited,
  });

  const [openFile, setOpenFile] = useState<WorkspaceFile | null>(null);
  const [showAll, setShowAll] = useState(false);

  function handleOpen(f: WorkspaceFile) {
    setOpenFile(f);
    onOpenFile?.(f);
  }

  function handleClose() {
    setOpenFile(null);
  }

  async function handleDownload(f: WorkspaceFile) {
    if (f.downloadUrl) {
      window.open(f.downloadUrl, '_blank');
      return;
    }

    // Mock‑Download
    const content = `Vorschau von ${f.name}\nID: ${f.id}\nNode: ${f.nodeId}`;
    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = f.name;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
    onDownloadFile?.(f);
  }

  const displayedFiles = showAll ? files : files.slice(0, maxVisible);
  const hasMore = files.length > maxVisible;

  return (
    <section aria-labelledby="workspace-files-heading" className="space-y-3 p-2">
      {/* Kopfzeile */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <h3 id="workspace-files-heading" className="text-sm font-medium text-text-soft dark:text-gray-300">
            Dateien
          </h3>
          {selectedNode && (
            <span className="text-xs text-text-muted dark:text-gray-500">
              ({selectedNode.name})
            </span>
          )}
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            className="rounded-lg p-1.5 text-text-muted transition hover:bg-surface-hover hover:text-text focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary dark:text-gray-500 dark:hover:bg-slate-800 dark:hover:text-gray-300"
            onClick={() => void reload()}
            disabled={isLoading}
            aria-label="Dateien neu laden"
            title="Neu laden"
          >
            <IconBadge icon={<RefreshCw />} size="sm" variant="default" />
          </button>

          {selectedNode && (
            <button
              type="button"
              className="flex items-center gap-1.5 rounded-lg bg-primary px-3 py-1.5 text-xs font-medium text-white shadow-glow transition hover:bg-primary-hover hover:shadow-primary-glow focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 dark:bg-primary/80 dark:hover:bg-primary"
              onClick={() => onUploadRequested?.(selectedNode.id)}
              aria-label="Datei hochladen"
            >
              <IconBadge icon={<Upload />} size="sm" variant="default" />
              <span>Hochladen</span>
            </button>
          )}
        </div>
      </div>

      {/* Lade-/Fehlerzustand */}
      {isLoading && (
        <div className="flex items-center gap-2 text-xs text-text-muted dark:text-gray-500">
          <span className="h-2 w-2 animate-pulse rounded-full bg-primary/60" />
          Dateien werden geladen …
        </div>
      )}

      {error && (
        <div className="rounded-lg border border-danger/20 bg-danger-soft px-3 py-2 text-xs text-danger dark:border-danger/30 dark:bg-danger/10">
          Dateien konnten nicht geladen werden.{' '}
          <button type="button" className="underline hover:no-underline" onClick={() => void reload()}>
            Erneut versuchen
          </button>
        </div>
      )}

      {!isLoading && !error && files.length === 0 && (
        <div className="flex flex-col items-center gap-2 rounded-lg border border-dashed border-border-soft py-6 text-center dark:border-white/10">
          <IconBadge icon={<FolderOpen />} size="lg" variant="default" />
          <span className="text-xs text-text-muted dark:text-gray-500">Keine Dateien in diesem Kontext.</span>
          {selectedNode && (
            <button
              type="button"
              className="text-xs text-primary hover:underline"
              onClick={() => onUploadRequested?.(selectedNode.id)}
            >
              Erste Datei hochladen
            </button>
          )}
        </div>
      )}

      {/* Dateiliste */}
      {!isLoading && !error && files.length > 0 && (
        <ul className="space-y-2">
          {displayedFiles.map((f) => {
            const inherited = f.inherited || false;
            return (
              <li
                key={f.id}
                className={[
                  'flex items-center gap-2 rounded-lg p-1.5 transition',
                  inherited ? 'bg-surface-muted/30 dark:bg-slate-800/20' : '',
                ].join(' ')}
              >
                {/* Icon */}
                <div className="shrink-0">
                  <IconBadge
                    icon={<WorkspaceFileIcon mimeType={f.mimeType} fileName={f.name} />}
                    size="sm"
                    variant="default"
                  />
                </div>

                {/* Name + Metadaten */}
                <div className="min-w-0 flex-1">
                  <div className="truncate text-sm font-medium text-text dark:text-white">{f.name}</div>
                  <div className="flex flex-wrap items-center gap-x-3 gap-y-0.5 text-xs text-text-muted dark:text-gray-500">
                    <span>{formatFileSize(f.size)}</span>
                    <span>·</span>
                    <span>{formatFileDate(f.updatedAt)}</span>
                    {inherited && (
                      <>
                        <span>·</span>
                        <span className="rounded bg-slate-200 px-1.5 py-0.5 text-[10px] dark:bg-slate-700/50">
                          Vererbt von {f.inheritedFromNodeName ?? f.inheritedFromNodeId}
                        </span>
                      </>
                    )}
                  </div>
                </div>

                {/* Aktionen */}
                <div className="flex shrink-0 items-center gap-1">
                  <button
                    type="button"
                    className="rounded px-2 py-1 text-xs font-medium text-primary transition hover:bg-primary-soft hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary dark:hover:bg-primary/10"
                    onClick={() => handleOpen(f)}
                    aria-label={`${f.name} öffnen`}
                  >
                    Öffnen
                  </button>
                  <button
                    type="button"
                    className="rounded px-2 py-1 text-xs font-medium text-text-muted transition hover:bg-surface-hover hover:text-text focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary dark:text-gray-400 dark:hover:bg-slate-800 dark:hover:text-white"
                    onClick={() => handleDownload(f)}
                    aria-label={`${f.name} herunterladen`}
                  >
                    Download
                  </button>
                </div>
              </li>
            );
          })}
        </ul>
      )}

      {/* "Alle anzeigen" Button */}
      {hasMore && (
        <button
          type="button"
          className="text-xs font-medium text-primary hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
          onClick={() => setShowAll((prev) => !prev)}
        >
          {showAll ? 'Weniger anzeigen' : `Alle ${files.length} Dateien anzeigen`}
        </button>
      )}

      {/* Modal für Dateivorschau */}
      <FileReaderModal file={openFile} isOpen={Boolean(openFile)} onClose={handleClose} />
    </section>
  );
}