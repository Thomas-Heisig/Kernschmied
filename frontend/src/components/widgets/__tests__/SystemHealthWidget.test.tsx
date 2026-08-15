import { render, screen, within } from '@testing-library/react';
import { vi } from 'vitest';
import { loadSystemOverview } from '../../../api/system';
import SystemHealthWidget from '../SystemHealthWidget';


vi.mock('../../../api/system', () => ({
  loadSystemOverview: vi.fn(),
}));


test('renders a successful database probe as online', async () => {
  vi.mocked(loadSystemOverview).mockResolvedValue({
    schema_version: '1.0',
    api_version: 'v1',
    status: 'ok',
    environment: 'development',
    config_revision: 3,
    security_profile: {},
    services: {
      config_service: { status: 'up' },
      model_registry: { status: 'up' },
      tool_registry: { status: 'up' },
      database: { status: 'up' },
    },
    registries: { models: 1, tools: 2 },
  });

  render(<SystemHealthWidget widget={{}} nodeId="system-root" />);

  const databaseLabel = await screen.findByText('Datenbank');
  const databaseRow = databaseLabel.parentElement;
  expect(databaseRow).not.toBeNull();
  expect(within(databaseRow as HTMLElement).getByText('Online')).toBeInTheDocument();
  expect(screen.getByText('1')).toBeInTheDocument();
  expect(screen.getByText('2')).toBeInTheDocument();
});