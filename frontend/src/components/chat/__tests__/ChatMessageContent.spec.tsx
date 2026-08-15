import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { ChatMessageContent } from '../ChatMessageContent';

describe('ChatMessageContent', () => {
  it('renders headings, lists, emphasis and GFM tables', () => {
    render(<ChatMessageContent content={'# Antrag\n\n**Wichtig**\n\n- Punkt A\n- Punkt B\n\n| Rolle | Name |\n|---|---|\n| Initiator | Marc |'} />);

    expect(screen.getByRole('heading', { name: 'Antrag' })).toBeInTheDocument();
    expect(screen.getByText('Wichtig').tagName).toBe('STRONG');
    expect(screen.getByRole('list')).toBeInTheDocument();
    expect(screen.getByRole('table')).toBeInTheDocument();
  });

  it('uses canonical media sizing and safe native media controls', () => {
    const { container } = render(<ChatMessageContent content={'![Foto](https://example.test/team.jpg)\n\n[Audio](https://example.test/hymne.mp3)\n\n[Video](https://example.test/spielzug.mp4)'} />);

    expect(screen.getByRole('img', { name: 'Foto' })).toHaveClass('max-h-144');
    expect(container.querySelector('audio[controls]')).toHaveAttribute('src', 'https://example.test/hymne.mp3');
    expect(container.querySelector('video[controls]')).toHaveClass('max-h-128');
  });

  it('marks placeholders and suppresses unsafe links', () => {
    render(<ChatMessageContent isAssistant content={"[Datum einfügen]\n\n[Unsicher](javascript:alert('x'))"} />);

    expect(screen.getByText(/Entwurf enthält noch Platzhalter/)).toBeInTheDocument();
    expect(screen.queryByRole('link', { name: 'Unsicher' })).not.toBeInTheDocument();
  });
});
