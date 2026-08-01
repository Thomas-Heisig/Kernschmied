-- Migration: Create calendars and events tables

CREATE TABLE IF NOT EXISTS calendars (
    id VARCHAR(36) PRIMARY KEY,
    owner_id VARCHAR(255),
    name VARCHAR(255) NOT NULL,
    color VARCHAR(20),
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_calendars_owner_id ON calendars(owner_id);

CREATE TABLE IF NOT EXISTS events (
    id VARCHAR(36) PRIMARY KEY,
    calendar_id VARCHAR(36) NOT NULL REFERENCES calendars(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    start TIMESTAMP WITH TIME ZONE NOT NULL,
    end TIMESTAMP WITH TIME ZONE NOT NULL,
    all_day BOOLEAN NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_events_calendar_start ON events(calendar_id, start);
