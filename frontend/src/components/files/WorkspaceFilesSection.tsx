import React from "react";
import { useWorkspaceFiles } from "../../hooks/useWorkspaceFiles";
import WorkspaceFileIcon from "./WorkspaceFileIcon";
import FileReaderModal from "./FileReaderModal";
import { formatFileDate, formatFileSize } from "../../utils/fileUtils";

import type { WorkspaceFile } from "../../contracts/workspace-files";

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

export default function WorkspaceFilesSection({ selectedNode, maxVisible = 5, includeInherited = false, onOpenFile, onDownloadFile, onUploadRequested }: Props) {
  const { files, isLoading, error, reload } = useWorkspaceFiles({ node: (selectedNode as any) ?? null, includeInherited });

  const [openFile, setOpenFile] = React.useState<WorkspaceFile | null>(null);

  function handleOpen(f: WorkspaceFile) {
    setOpenFile(f);
  }

  function handleClose() {
    setOpenFile(null);
  }

  async function handleDownload(f: WorkspaceFile) {
    if (f.downloadUrl) {
      window.open(f.downloadUrl, '_blank');
      return;
    }

    // generate deterministic mock content
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
  }

  return (
    <section aria-labelledby="workspace-files-heading" className="p-2">
      <h3 id="workspace-files-heading" className="text-sm font-medium">
        Dateien
      </h3>

      {selectedNode ? (
        <div className="text-xs text-text-muted">Kontext: {selectedNode.name}</div>
      ) : (
        <div className="text-xs text-text-muted">Kein Kontext ausgewählt</div>
      )}

      {isLoading && <div className="text-xs text-muted-foreground">Dateien werden geladen…</div>}
      {error && (
        <div className="text-xs text-red-600">Dateien konnten nicht geladen werden. <button className="underline" onClick={() => void reload()}>Erneut versuchen</button></div>
      )}

      {!isLoading && !error && files.length === 0 && (
        <div className="text-xs text-muted-foreground">Keine Dateien in diesem Kontext.</div>
      )}

      <ul className="mt-2 space-y-2">
        {files.slice(0, maxVisible).map((f) => (
          <li key={f.id} className="flex items-center gap-2">
            <WorkspaceFileIcon mimeType={f.mimeType} fileName={f.name} className="w-5 h-5 text-slate-600" />
            <div className="flex-1 min-w-0">
              <div className="text-sm truncate">{f.name}</div>
              <div className="text-xs text-muted-foreground">
                {formatFileSize(f.size)} · {formatFileDate(f.updatedAt)} {f.inherited ? `· Aus: ${f.inheritedFromNodeName ?? f.inheritedFromNodeId}` : ''}
              </div>
            </div>
            <div className="flex gap-2">
              <button className="text-xs text-blue-600" onClick={() => handleOpen(f)}>
                Öffnen
              </button>
              <button className="text-xs text-blue-600" onClick={() => handleDownload(f)}>
                Herunterladen
              </button>
            </div>
          </li>
        ))}
      </ul>

      {files.length > maxVisible && (
        <div className="mt-2">
          <button className="text-xs text-blue-600">Alle Dateien anzeigen</button>
        </div>
      )}

      <div className="mt-2 flex items-center justify-between">
        <button className="text-xs" onClick={() => void reload()}>
          Aktualisieren
        </button>
        {selectedNode && (
          <button className="text-xs text-white bg-primary px-2 py-1 rounded" onClick={() => onUploadRequested?.(selectedNode.id)}>
            + Datei hinzufügen
          </button>
        )}
      </div>
      <FileReaderModal file={openFile} isOpen={Boolean(openFile)} onClose={handleClose} />
    </section>
  );
}
