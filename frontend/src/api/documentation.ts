import { apiGet } from "./client";
import type {
  DocumentationIndexResponse,
  DocumentationPageResponse,
} from "../contracts/documentation";

export function loadDocumentationIndex(
  signal?: AbortSignal,
): Promise<DocumentationIndexResponse> {
  return apiGet<DocumentationIndexResponse>("/documentation", { signal });
}

export function loadDocumentationPage(
  pageId: string,
  signal?: AbortSignal,
): Promise<DocumentationPageResponse> {
  const encodedPageId = encodeURIComponent(pageId);

  return apiGet<DocumentationPageResponse>(
    `/documentation/pages/${encodedPageId}`,
    { signal },
  );
}
