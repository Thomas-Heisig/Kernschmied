import { AlertTriangle, FileText } from 'lucide-react';
import Markdown, { type Components } from 'react-markdown';
import remarkGfm from 'remark-gfm';

const AUDIO_EXTENSION = /\.(mp3|m4a|ogg|opus|wav)(?:[?#].*)?$/i;
const VIDEO_EXTENSION = /\.(mp4|m4v|webm|ogv|mov)(?:[?#].*)?$/i;
const PLACEHOLDER = /\[(?:[^\]]*(?:einfügen|ergänzen|kontakt|datum|name|adresse)[^\]]*)\]/i;

function safeResourceUrl(value: string | undefined): string | undefined {
  if (!value) return undefined;
  if (value.startsWith('/')) return value;
  try {
    const url = new URL(value);
    return url.protocol === 'https:' || url.protocol === 'http:' ? value : undefined;
  } catch {
    return undefined;
  }
}

const components: Components = {
  h1: ({ children }) => <h1 className="mb-3 mt-6 text-xl font-bold tracking-tight first:mt-1">{children}</h1>,
  h2: ({ children }) => <h2 className="mb-2 mt-5 border-b border-current/15 pb-1.5 text-lg font-semibold first:mt-1">{children}</h2>,
  h3: ({ children }) => <h3 className="mb-2 mt-4 text-base font-semibold first:mt-1">{children}</h3>,
  p: ({ children }) => <p className="my-2 whitespace-pre-wrap wrap-break-words text-sm leading-7">{children}</p>,
  strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
  ul: ({ children }) => <ul className="my-3 list-disc space-y-1.5 pl-6 text-sm leading-6 marker:text-current">{children}</ul>,
  ol: ({ children }) => <ol className="my-3 list-decimal space-y-1.5 pl-6 text-sm leading-6 marker:font-semibold marker:text-current">{children}</ol>,
  li: ({ children }) => <li className="pl-1">{children}</li>,
  blockquote: ({ children }) => <blockquote className="my-4 border-l-4 border-current/40 bg-black/5 px-4 py-2 dark:bg-white/5">{children}</blockquote>,
  hr: () => <hr className="my-5 border-current/15" />,
  table: ({ children }) => <div className="my-4 overflow-x-auto rounded-xl border border-current/15"><table className="min-w-full border-collapse text-left text-sm">{children}</table></div>,
  thead: ({ children }) => <thead className="bg-black/10 text-xs uppercase tracking-wide dark:bg-white/10">{children}</thead>,
  tbody: ({ children }) => <tbody className="divide-y divide-current/15">{children}</tbody>,
  tr: ({ children }) => <tr className="transition-colors hover:bg-black/5 dark:hover:bg-white/5">{children}</tr>,
  th: ({ children }) => <th className="whitespace-nowrap px-3 py-2.5 font-semibold">{children}</th>,
  td: ({ children }) => <td className="px-3 py-2.5 align-top">{children}</td>,
  pre: ({ children }) => <pre className="my-4 overflow-x-auto rounded-xl bg-slate-950 p-4 text-xs leading-6 text-slate-100 shadow-inner">{children}</pre>,
  code: ({ className, children }) => className ? <code className={`${className} font-mono`}>{children}</code> : <code className="rounded bg-black/10 px-1.5 py-0.5 font-mono text-[0.9em] dark:bg-white/10">{children}</code>,
  a: ({ href, children }) => {
    const safeHref = safeResourceUrl(href);
    if (!safeHref) return <span>{children}</span>;
    if (AUDIO_EXTENSION.test(safeHref)) {
      return <span className="my-3 block rounded-xl border border-current/15 bg-black/5 p-3 dark:bg-white/5"><span className="mb-2 block text-xs font-semibold">{children}</span><audio controls preload="metadata" className="w-full" src={safeHref}>Audio wird vom Browser nicht unterstützt.</audio></span>;
    }
    if (VIDEO_EXTENSION.test(safeHref)) {
      return <span className="my-3 block overflow-hidden rounded-xl border border-current/15 bg-black"><video controls preload="metadata" className="max-h-128 w-full" src={safeHref}>Video wird vom Browser nicht unterstützt.</video><span className="block bg-slate-950 px-3 py-2 text-xs text-slate-200">{children}</span></span>;
    }
    return <a href={safeHref} target="_blank" rel="noreferrer" className="font-medium underline decoration-current/40 underline-offset-4 hover:decoration-current">{children}</a>;
  },
  img: ({ src, alt }) => {
    const safeSrc = safeResourceUrl(typeof src === 'string' ? src : undefined);
    if (!safeSrc) return null;
    return <span className="my-4 block overflow-hidden rounded-xl border border-current/15 bg-black/5 dark:bg-white/5"><img src={safeSrc} alt={alt ?? ''} loading="lazy" className="max-h-144 w-full object-contain" />{alt ? <span className="block border-t border-current/15 px-3 py-2 text-xs">{alt}</span> : null}</span>;
  },
};

export interface ChatMessageContentProps {
  content: string;
  isAssistant?: boolean;
}

export function ChatMessageContent({ content, isAssistant = false }: ChatMessageContentProps) {
  const hasPlaceholder = isAssistant && PLACEHOLDER.test(content);

  return (
    <div className="chat-message-content min-w-0">
      <Markdown remarkPlugins={[remarkGfm]} components={components} skipHtml>
        {content}
      </Markdown>
      {isAssistant ? (
        <div className={`mt-4 flex items-start gap-2 rounded-lg border px-3 py-2 text-xs ${hasPlaceholder ? 'border-amber-600/40 bg-amber-50 text-amber-950 dark:bg-amber-950/30 dark:text-amber-200' : 'border-slate-300 bg-slate-50 text-slate-700 dark:border-white/10 dark:bg-slate-900/40 dark:text-gray-300'}`}>
          {hasPlaceholder ? <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" /> : <FileText className="mt-0.5 h-4 w-4 shrink-0" />}
          <span>{hasPlaceholder ? 'Entwurf enthält noch Platzhalter. Vor der Verwendung Namen, Datum, Kontakte, Zahlen und Tatsachen prüfen.' : 'KI-Entwurf: Wichtige Namen, Zahlen, Termine und externe Tatsachen vor der Verwendung prüfen.'}</span>
        </div>
      ) : null}
    </div>
  );
}

export default ChatMessageContent;
