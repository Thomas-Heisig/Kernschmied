export interface CalendarSelectionRequest {
  selected: string; // ISO timestamp
  note?: string | null;
}

export interface CalendarSelectionResponse {
  id: string;
  selected: string;
  note?: string | null;
  created_at: string;
}
