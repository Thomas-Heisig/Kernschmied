// F:\Kernschmied\frontend\src\components\widgets\FilesWidget.tsx

import React, { useEffect, useState } from 'react';
import { File, RefreshCw, AlertCircle, Download, ExternalLink } from 'lucide-react';
import IconBadge from '../common/IconBadge';
import WorkspaceFileIcon from '../files/WorkspaceFileIcon';
import { formatFileSize } from '../../utils/fileUtils';

interface FilesWidgetProps {
  widget?: any;
  nodeId?: string;
}

interface FileItem {
  id?: string;
  name?: string;
  filename?: string;
  size?: number;
  mimeType?: string;
  url?: string;
  path?: string;
  downloadUrl?: string;
  updatedAt?: string;
}

export default function FilesWidget({ widget, nodeId }: FilesWidgetProps) {
  const [files, setFiles] = useState<FileItem[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const loadFiles = async (showRefresh = false) => {
    if (showRefresh) setIsRefreshing(true);
    setError(null);

    try {
      if (!nodeId) throw new Error('Kein Dateikontext ausgewählt.');
      const params = new URLSearchParams({ node_id: nodeId });
      const res = await fetch(`/api/v1/files?${params.toString()}`, { credentials: 'include' });
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}: ${res.statusText}`);
      }
      const j = await res.json();
      const items = Array.isArray(j) ? j : j.items ?? [];
      setFiles(
        items.map((it: any) => ({
          id: it.id,
          name: it.name ?? it.filename ?? String(it),
          filename: it.filename ?? it.name,
          size: it.size,
          mimeType: it.mimeType ?? it.mime_type,
          url: it.url ?? it.path ?? null,
          downloadUrl: it.downloadUrl ?? it.download_url ?? null,
          updatedAt: it.updatedAt ?? it.updated_at ?? it.modified,
        }))
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Dateien konnten nicht geladen werden.');
      setFiles(null);
    } finally {
      if (showRefresh) setIsRefreshing(false);
      setLoading(false);
    }
  };

  useEffect(() => {
    setLoading(true);
    void loadFiles(false);
  }, [nodeId]);

  const formatDate = (date?: string) => {
    if (!date) return '—';
    try {
      return new Date(date).toLocaleString('de-DE', {
        dateStyle: 'short',
        timeStyle: 'short',
      });
    } catch {
      return date;
    }
  };

  return (
    <div className="rounded-xl border border-border-soft bg-white/90 p-4 shadow-sm backdrop-blur-sm dark:border-white/10 dark:bg-slate-900/80">
      {/* Kopfzeile */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2.5">
          <IconBadge icon={<File />} size="md" variant="primary" />
          <h3 className="text-sm font-semibold text-text dark:text-white">Dateien</h3>
          {files && (
            <span className="rounded-full bg-surface-muted px-2 py-0.5 text-xs text-text-muted dark:bg-slate-800 dark:text-gray-400">
              {files.length}
            </span>
          )}
        </div>
        <button
          type="button"
          className="rounded-lg p-1.5 text-text-muted transition hover:bg-surface-hover hover:text-text focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary dark:text-gray-400 dark:hover:bg-slate-800 dark:hover:text-white"
          onClick={() => void loadFiles(true)}
          disabled={isRefreshing}
          aria-label="Dateien neu laden"
          title="Neu laden"
        >
          <IconBadge icon={<RefreshCw className={isRefreshing ? 'animate-spin' : ''} />} size="sm" variant="default" />
        </button>
      </div>

      {/* Inhalt */}
      {loading ? (
        <div className="flex items-center gap-2 py-4 text-sm text-text-muted dark:text-gray-400">
          <span className="h-2 w-2 animate-pulse rounded-full bg-primary/60" />
          Lade Dateien …
        </div>
      ) : error ? (
        <div className="flex items-start gap-2 rounded-lg border border-danger/20 bg-danger-soft px-3 py-2 text-sm text-danger dark:border-danger/30 dark:bg-danger/10">
          <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      ) : files && files.length > 0 ? (
        <div className="space-y-2 max-h-64 overflow-y-auto">
          {files.slice(0, 20).map((file, idx) => {
            const name = file.name ?? file.filename ?? 'Unbenannt';
            const fileSize = file.size ? formatFileSize(file.size) : null;
            const hasUrl = file.url || file.downloadUrl;

            return (
              <div
                key={file.id ?? idx}
                className="flex items-center gap-2.5 rounded-lg border border-border-soft/50 px-3 py-2 transition-colors hover:bg-surface-hover dark:border-white/5 dark:hover:bg-slate-800/50"
              >
                {/* Datei‑Icon */}
                <div className="shrink-0">
                  <WorkspaceFileIcon
                    mimeType={file.mimeType}
                    fileName={name}
                    className="h-5 w-5 text-text-muted dark:text-gray-500"
                  />
                </div>

                {/* Name + Metadaten */}
                <div className="min-w-0 flex-1">
                  <div className="truncate text-sm font-medium text-text dark:text-white">{name}</div>
                  <div className="flex items-center gap-3 text-xs text-text-muted dark:text-gray-500">
                    {fileSize && <span>{fileSize}</span>}
                    {file.updatedAt && (
                      <>
                        {fileSize && <span>·</span>}
                        <span>{formatDate(file.updatedAt)}</span>
                      </>
                    )}
                  </div>
                </div>

                {/* Aktionen */}
                {hasUrl && (
                  <a
                    href={file.url ?? file.downloadUrl ?? '#'}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="shrink-0 rounded-lg p-1.5 text-text-muted transition hover:bg-surface-hover hover:text-primary dark:text-gray-400 dark:hover:bg-slate-800 dark:hover:text-primary"
                    aria-label={`${name} öffnen`}
                    title="Öffnen"
                  >
                    {file.downloadUrl ? (
                      <IconBadge icon={<Download />} size="sm" variant="default" />
                    ) : (
                      <IconBadge icon={<ExternalLink />} size="sm" variant="default" />
                    )}
                  </a>
                )}
              </div>
            );
          })}
          {files.length > 20 && (
            <div className="text-xs text-text-muted dark:text-gray-400">
              +{files.length - 20} weitere Dateien
            </div>
          )}
        </div>
      ) : (
        <div className="flex flex-col items-center gap-2 py-6 text-center">
          <IconBadge icon={<File />} size="lg" variant="default" />
          <span className="text-sm text-text-muted dark:text-gray-400">Keine Dateien gefunden.</span>
        </div>
      )}
    </div>
  );
}