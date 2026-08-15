// F:\Kernschmied\frontend\src\components\files\WorkspaceFileIcon.tsx

import {
  Braces,
  File,
  FileArchive,
  FileAudio,
  FileCode,
  FileImage,
  FileSpreadsheet,
  FileText,
  FileVideo,
} from 'lucide-react';
import type { LucideIcon } from 'lucide-react';

interface WorkspaceFileIconProps {
  mimeType?: string;
  fileName?: string;
  className?: string;
}

function getFileExtension(name?: string): string | null {
  if (!name) return null;
  const parts = name.split('.');
  return parts.length > 1 ? parts.pop()?.toLowerCase() ?? null : null;
}

/**
 * Gibt das passende Lucide‑Icon für einen Dateityp zurück.
 * Die Icon‑Komponente wird als React‑Element zurückgegeben – kann in IconBadge eingebettet werden.
 */
export default function WorkspaceFileIcon({ mimeType, fileName, className }: WorkspaceFileIconProps) {
  const mt = mimeType || '';
  const ext = getFileExtension(fileName) || '';

  let IconComponent: LucideIcon = File;

  // Bilder
  if (mt.startsWith('image/')) IconComponent = FileImage;
  // PDF
  else if (mt === 'application/pdf') IconComponent = FileText;
  // Video
  else if (mt.startsWith('video/')) IconComponent = FileVideo;
  // Audio
  else if (mt.startsWith('audio/')) IconComponent = FileAudio;
  // Archive
  else if (
    mt === 'application/zip' ||
    mt === 'application/x-zip-compressed' ||
    ['zip', 'rar', '7z', 'gz', 'tar'].includes(ext)
  )
    IconComponent = FileArchive;
  // Code / strukturierte Formate
  else if (
    mt === 'application/javascript' ||
    mt === 'application/typescript' ||
    ['js', 'ts', 'py', 'xml', 'html', 'htm', 'css', 'scss', 'sql'].includes(ext)
  )
    IconComponent = FileCode;
  // JSON / YAML
  else if (mt === 'application/json' || ext === 'json' || ext === 'yaml' || ext === 'yml')
    IconComponent = Braces;
  // Tabellen / CSV
  else if (mt === 'text/csv' || ext === 'csv' || ext === 'xls' || ext === 'xlsx')
    IconComponent = FileSpreadsheet;
  // Text
  else if (mt.startsWith('text/') || ['txt', 'md', 'log'].includes(ext))
    IconComponent = FileText;

  return <IconComponent className={className} />;
}