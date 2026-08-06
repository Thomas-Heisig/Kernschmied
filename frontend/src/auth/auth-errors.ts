export function getAuthErrorMessage(error: unknown): string {
  try {
    if (!error) return 'Unbekannter Fehler';
    // ApiError shape: { message?: string } or has status/code
    const anyErr = error as any;
    if (typeof anyErr === 'string') return anyErr;
    if (typeof anyErr?.message === 'string' && anyErr.message.length) return anyErr.message;
    if (typeof anyErr?.detail === 'string' && anyErr.detail.length) return anyErr.detail;
    if (anyErr?.detail && typeof anyErr.detail === 'object' && typeof anyErr.detail.message === 'string') return anyErr.detail.message;
    return 'Ein Fehler ist aufgetreten';
  } catch {
    return 'Ein Fehler ist aufgetreten';
  }
}
