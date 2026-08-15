import type { SystemOverviewResponse } from '../contracts/system';
import { apiGet } from './client';

export function loadSystemOverview(signal?: AbortSignal): Promise<SystemOverviewResponse> {
  return apiGet<SystemOverviewResponse>('/system/overview', { signal });
}