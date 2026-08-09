import React from "react";
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
} from "lucide-react";

interface WorkspaceFileIconProps {
  mimeType?: string;
  fileName?: string;
  className?: string;
}

function ext(name?: string): string | null {
  if (!name) return null;
  const m = name.split(".").pop();
  return m ? m.toLowerCase() : null;
}

export default function WorkspaceFileIcon({ mimeType, fileName, className }: WorkspaceFileIconProps) {
  const mt = mimeType || "";
  const e = ext(fileName) || "";

  if (mt.startsWith("image/")) return <FileImage className={className} />;
  if (mt === "application/pdf") return <FileText className={className} />;
  if (mt.startsWith("video/")) return <FileVideo className={className} />;
  if (mt.startsWith("audio/")) return <FileAudio className={className} />;
  if (mt === "application/zip" || mt === "application/x-zip-compressed" || e === "zip" || e === "rar" || e === "7z") return <FileArchive className={className} />;

  // code and structured formats
  if (mt === "application/javascript" || e === "js") return <FileCode className={className} />;
  if (mt === "application/typescript" || e === "ts") return <FileCode className={className} />;
  if (mt === "application/json" || e === "json") return <Braces className={className} />;
  if (e === "py") return <FileCode className={className} />;
  if (e === "xml") return <FileCode className={className} />;
  if (e === "html" || e === "htm") return <FileCode className={className} />;
  if (e === "css") return <File className={className} />;
  if (e === "csv" || mt === "text/csv") return <File className={className} />;
  if (e === "dxf") return <File className={className} />;

  if (mt.startsWith("text/")) return <FileText className={className} />;

  return <File className={className} />;
}
