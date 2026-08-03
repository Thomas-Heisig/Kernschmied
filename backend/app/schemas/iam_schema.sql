-- IAM Registry schema (initial MVP)

CREATE TABLE IF NOT EXISTS identity_providers (
    id UUID PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    config JSONB,
    claim_mapping JSONB,
    sync_enabled BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE TABLE IF NOT EXISTS identities (
    id UUID PRIMARY KEY,
    type TEXT NOT NULL,
    principal TEXT NOT NULL,
    display_name TEXT,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE TABLE IF NOT EXISTS permissions (
    id TEXT PRIMARY KEY,
    description TEXT,
    resource_kind TEXT,
    scope_levels TEXT[],
    schema_version TEXT DEFAULT '1.0',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE TABLE IF NOT EXISTS roles (
    id UUID PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    permissions TEXT[] NOT NULL,
    schema_version TEXT DEFAULT '1.0',
    revision INTEGER DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE TABLE IF NOT EXISTS policies (
    id UUID PRIMARY KEY,
    name TEXT NOT NULL,
    scope_level TEXT,
    scope_id TEXT,
    expression JSONB,
    effect TEXT CHECK (effect IN ('allow','deny')) DEFAULT 'deny',
    precedence INTEGER DEFAULT 100,
    schema_version TEXT DEFAULT '1.0',
    revision INTEGER DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Basic audit table for decisions
CREATE TABLE IF NOT EXISTS authorization_audit (
    id UUID PRIMARY KEY,
    request_id UUID,
    identity_id UUID,
    permission TEXT,
    scope_level TEXT,
    scope_id TEXT,
    decision BOOLEAN,
    reason TEXT,
    trace JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);
