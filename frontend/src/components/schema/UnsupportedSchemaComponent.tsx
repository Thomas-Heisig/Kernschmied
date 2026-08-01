import React from 'react';

export interface UnsupportedProps {
  type?: string;
  definition?: any;
}

export default function UnsupportedSchemaComponent({ type, definition }: UnsupportedProps) {
  return (
    <div className="rounded border border-red-200 bg-red-50 p-3 text-sm text-red-800">
      <strong>Nicht unterstützt:</strong> {type}
      <pre className="mt-2 max-h-48 overflow-auto rounded bg-white p-2 text-xs text-slate-800">
        {JSON.stringify(definition ?? {}, null, 2)}
      </pre>
    </div>
  );
}
