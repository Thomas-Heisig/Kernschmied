import { apiGet, apiPatch } from './client';

export type PromptSource = {
  node_id: string;
  node_name?: string | null;
  node_type?: string | null;
  local_prompt?: string | null;
  prompt_length: number;
  is_target: boolean;
};

export type PromptContext = {
  schema_version: string;
  node_id: string;
  local_prompt?: string | null;
  sources: PromptSource[];
  effective_prompt?: string | null;
  effective_prompt_length?: number;
};

export async function loadPromptContext(nodeId: string) {
  return apiGet<PromptContext>(`/hierarchy/${encodeURIComponent(nodeId)}/prompt-context`);
}

export async function saveLocalPrompt(nodeId: string, prompt: string | null) {
  return apiPatch(`/hierarchy/${encodeURIComponent(nodeId)}`, { system_prompt: prompt });
}

export default { loadPromptContext, saveLocalPrompt };
