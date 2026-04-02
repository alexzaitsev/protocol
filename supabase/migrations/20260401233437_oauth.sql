-- Copyright 2026 Alex Zaitsev
-- SPDX-License-Identifier: AGPL-3.0-only

CREATE TABLE IF NOT EXISTS public.google_oauth (
    collection TEXT NOT NULL,
    key TEXT NOT NULL,
    value JSONB NOT NULL,
    ttl DOUBLE PRECISION,
    created_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ,
    PRIMARY KEY (collection, key)
);

CREATE INDEX IF NOT EXISTS idx_google_oauth_expires_at
    ON public.google_oauth (expires_at)
    WHERE expires_at IS NOT NULL;

-- No policies: only the postgres superuser (MCP server) should access this table.
ALTER TABLE public.google_oauth ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON public.google_oauth FROM anon, authenticated;
