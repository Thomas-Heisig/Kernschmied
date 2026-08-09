export function formatFileSize(bytes: number): string {
  if (!Number.isFinite(bytes) || bytes < 0) return "0 B";

  const thresh = 1024;
  if (bytes < thresh) return `${bytes} B`;

  const units = ["KB", "MB", "GB", "TB"];
  let u = -1;
  let value = bytes;

  do {
    value = value / thresh;
    u++;
  } while (value >= thresh && u < units.length - 1);

  return `${value.toFixed(value >= 10 ? 0 : 1)} ${units[u]}`;
}

export function formatFileDate(value: string): string {
  try {
    const d = new Date(value);
    if (!isFinite(d.getTime())) return "";
    return new Intl.DateTimeFormat("de-DE", {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    }).format(d);
  } catch (e) {
    return "";
  }
}
