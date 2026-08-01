-- SQL Migration: Create calendar_selections table
-- Run manually if you manage DB migrations outside of ORM create_all.

CREATE TABLE IF NOT EXISTS calendar_selections (
    id TEXT PRIMARY KEY,
    user_id TEXT,
    selected_at TIMESTAMP,
    note TEXT,
    created_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_calendar_selected_at ON calendar_selections(selected_at);
