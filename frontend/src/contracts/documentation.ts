export interface DocumentationPageSummary {
  id: string;
  title: string;
  description: string;
}

export interface DocumentationSection {
  id: string;
  title: string;
  pages: DocumentationPageSummary[];
}

export interface DocumentationIndexResponse {
  schema_version: '1.0';
  default_page_id: string | null;
  sections: DocumentationSection[];
}

export interface DocumentationPageResponse {
  schema_version: '1.0';
  id: string;
  title: string;
  section_id: string;
  section_title: string;
  content: string;
}
