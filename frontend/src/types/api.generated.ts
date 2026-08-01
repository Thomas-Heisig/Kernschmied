// Auto-generated minimal API types (generated from OpenAPI)
export interface CalendarCreate {
  name: string;
  color?: string | null;
  description?: string | null;
}

export interface CalendarOut {
  id: string;
  name: string;
  color?: string | null;
  description?: string | null;
  owner_id: string;
  created_at: string;
  updated_at: string;
}

export interface EventCreate {
  title: string;
  description?: string | null;
  start: string; // ISO datetime
  end: string; // ISO datetime
  all_day?: boolean | null;
}

export interface EventOut {
  id: string;
  calendar_id: string;
  title: string;
  description?: string | null;
  start: string;
  end: string;
  all_day: boolean;
  created_at: string;
  updated_at: string;
}
