import type { ReactNode } from 'react';

interface MarkdownDocumentProps {
  content: string;
}

type Block =
  | { type: 'heading'; level: number; text: string }
  | { type: 'paragraph'; text: string }
  | { type: 'code'; language: string; text: string }
  | { type: 'list'; ordered: boolean; items: string[] }
  | { type: 'quote'; text: string }
  | { type: 'rule' };

export function MarkdownDocument({ content }: MarkdownDocumentProps) {
  const blocks = parseMarkdown(content);

  return (
    <article className="mx-auto w-full max-w-4xl px-5 py-8 sm:px-8 lg:px-12">
      {blocks.map((block, index) => renderBlock(block, index))}
    </article>
  );
}

function renderBlock(block: Block, index: number): ReactNode {
  const key = `${block.type}-${index}`;

  if (block.type === 'heading') {
    const className =
      block.level === 1
        ? 'mb-5 mt-1 text-3xl font-semibold tracking-tight text-text dark:text-white'
        : block.level === 2
          ? 'mb-3 mt-9 text-2xl font-semibold tracking-tight text-text dark:text-white'
          : 'mb-2 mt-7 text-lg font-semibold text-text dark:text-white';

    if (block.level === 1)
      return (
        <h1 key={key} className={className}>
          {renderInline(block.text)}
        </h1>
      );
    if (block.level === 2)
      return (
        <h2 key={key} className={className}>
          {renderInline(block.text)}
        </h2>
      );
    return (
      <h3 key={key} className={className}>
        {renderInline(block.text)}
      </h3>
    );
  }

  if (block.type === 'paragraph') {
    return (
      <p key={key} className="my-4 leading-7 text-text-soft dark:text-slate-300">
        {renderInline(block.text)}
      </p>
    );
  }

  if (block.type === 'code') {
    return (
      <div
        key={key}
        className="my-6 overflow-hidden rounded-xl border border-border bg-slate-950 shadow-sm dark:border-white/10"
      >
        {block.language ? (
          <div className="border-b border-white/10 px-4 py-2 font-mono text-[11px] uppercase tracking-wider text-slate-400">
            {block.language}
          </div>
        ) : null}
        <pre className="overflow-x-auto p-4 text-sm leading-6 text-slate-100">
          <code>{block.text}</code>
        </pre>
      </div>
    );
  }

  if (block.type === 'list') {
    const ListTag = block.ordered ? 'ol' : 'ul';
    return (
      <ListTag
        key={key}
        className={[
          'my-4 space-y-2 pl-6 leading-7 text-text-soft dark:text-slate-300',
          block.ordered ? 'list-decimal' : 'list-disc',
        ].join(' ')}
      >
        {block.items.map((item, itemIndex) => (
          <li key={`${key}-${itemIndex}`}>{renderInline(item)}</li>
        ))}
      </ListTag>
    );
  }

  if (block.type === 'quote') {
    return (
      <blockquote
        key={key}
        className="my-6 rounded-r-xl border-l-4 border-primary bg-primary/5 px-5 py-4 leading-7 text-text-soft dark:bg-primary/10 dark:text-slate-300"
      >
        {renderInline(block.text)}
      </blockquote>
    );
  }

  return <hr key={key} className="my-8 border-border dark:border-white/10" />;
}

function renderInline(text: string): ReactNode[] {
  const parts = text.split(/(`[^`]+`|\*\*[^*]+\*\*|\[[^\]]+\]\([^)]+\))/g);

  return parts.map((part, index) => {
    if (part.startsWith('`') && part.endsWith('`')) {
      return (
        <code
          key={index}
          className="rounded-md bg-surface-muted px-1.5 py-0.5 font-mono text-[0.9em] text-primary dark:bg-slate-800 dark:text-primary"
        >
          {part.slice(1, -1)}
        </code>
      );
    }

    if (part.startsWith('**') && part.endsWith('**')) {
      return (
        <strong key={index} className="font-semibold text-text dark:text-white">
          {part.slice(2, -2)}
        </strong>
      );
    }

    const linkMatch = /^\[([^\]]+)\]\(([^)]+)\)$/.exec(part);
    if (linkMatch) {
      const href = linkMatch[2];
      const safeHref = href.startsWith('http://') || href.startsWith('https://') ? href : undefined;

      return safeHref ? (
        <a
          key={index}
          href={safeHref}
          target="_blank"
          rel="noreferrer"
          className="font-medium text-primary underline decoration-primary/30 underline-offset-4 hover:decoration-primary"
        >
          {linkMatch[1]}
        </a>
      ) : (
        <span key={index}>{linkMatch[1]}</span>
      );
    }

    return <span key={index}>{part}</span>;
  });
}

function parseMarkdown(content: string): Block[] {
  const lines = content.replace(/\r\n/g, '\n').split('\n');
  const blocks: Block[] = [];
  let index = 0;

  while (index < lines.length) {
    const line = lines[index];

    if (!line.trim()) {
      index += 1;
      continue;
    }

    if (line.startsWith('```')) {
      const language = line.slice(3).trim();
      const codeLines: string[] = [];
      index += 1;
      while (index < lines.length && !lines[index].startsWith('```')) {
        codeLines.push(lines[index]);
        index += 1;
      }
      index += 1;
      blocks.push({ type: 'code', language, text: codeLines.join('\n') });
      continue;
    }

    const headingMatch = /^(#{1,3})\s+(.+)$/.exec(line);
    if (headingMatch) {
      blocks.push({
        type: 'heading',
        level: headingMatch[1].length,
        text: headingMatch[2].trim(),
      });
      index += 1;
      continue;
    }

    if (/^\s*([-*_])\1\1+\s*$/.test(line)) {
      blocks.push({ type: 'rule' });
      index += 1;
      continue;
    }

    if (line.startsWith('>')) {
      const quoteLines: string[] = [];
      while (index < lines.length && lines[index].startsWith('>')) {
        quoteLines.push(lines[index].replace(/^>\s?/, ''));
        index += 1;
      }
      blocks.push({ type: 'quote', text: quoteLines.join(' ') });
      continue;
    }

    const listMatch = /^\s*(?:([-*+])|(\d+)\.)\s+(.+)$/.exec(line);
    if (listMatch) {
      const ordered = Boolean(listMatch[2]);
      const items: string[] = [];
      while (index < lines.length) {
        const itemMatch = /^\s*(?:([-*+])|(\d+)\.)\s+(.+)$/.exec(lines[index]);
        if (!itemMatch || Boolean(itemMatch[2]) !== ordered) break;
        items.push(itemMatch[3].trim());
        index += 1;
      }
      blocks.push({ type: 'list', ordered, items });
      continue;
    }

    const paragraphLines = [line.trim()];
    index += 1;
    while (index < lines.length && lines[index].trim() && !isBlockStart(lines[index])) {
      paragraphLines.push(lines[index].trim());
      index += 1;
    }
    blocks.push({ type: 'paragraph', text: paragraphLines.join(' ') });
  }

  return blocks;
}

function isBlockStart(line: string): boolean {
  return (
    line.startsWith('```') ||
    /^(#{1,3})\s+/.test(line) ||
    line.startsWith('>') ||
    /^\s*(?:[-*+]|\d+\.)\s+/.test(line) ||
    /^\s*([-*_])\1\1+\s*$/.test(line)
  );
}