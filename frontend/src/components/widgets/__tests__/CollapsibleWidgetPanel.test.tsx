import { fireEvent, render, screen } from '@testing-library/react';
import CollapsibleWidgetPanel from '../CollapsibleWidgetPanel';


test('collapses and restores widget content', () => {
  render(
    <CollapsibleWidgetPanel title="Systemwidgets" icon={<span>W</span>}>
      <p>Widget-Inhalt</p>
    </CollapsibleWidgetPanel>,
  );

  const toggle = screen.getByRole('button', { name: /Systemwidgets/ });
  expect(toggle).toHaveAttribute('aria-expanded', 'true');
  expect(screen.getByText('Widget-Inhalt')).toBeInTheDocument();

  fireEvent.click(toggle);
  expect(toggle).toHaveAttribute('aria-expanded', 'false');
  expect(screen.queryByText('Widget-Inhalt')).not.toBeInTheDocument();

  fireEvent.click(toggle);
  expect(toggle).toHaveAttribute('aria-expanded', 'true');
  expect(screen.getByText('Widget-Inhalt')).toBeInTheDocument();
});