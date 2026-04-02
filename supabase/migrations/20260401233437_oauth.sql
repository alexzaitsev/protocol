-- Copyright 2026 Alex Zaitsev
-- SPDX-License-Identifier: AGPL-3.0-only
CREATE TABLE IF NOT EXISTS public.google_oauth(
  collection text NOT NULL,
  key TEXT NOT NULL,
  value jsonb NOT NULL,
  ttl double precision,
  created_at timestamptz,
  expires_at timestamptz,
  PRIMARY KEY (collection, key)
);

CREATE INDEX IF NOT EXISTS idx_google_oauth_expires_at ON public.google_oauth(expires_at)
WHERE
  expires_at IS NOT NULL;

-- No policies: only the postgres superuser (MCP server) should access this table.
ALTER TABLE public.google_oauth ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
  IF EXISTS(
    SELECT
    FROM
      pg_catalog.pg_roles
    WHERE
      rolname = 'anon') THEN
  REVOKE ALL ON public.google_oauth FROM anon;
END IF;
  IF EXISTS(
    SELECT
    FROM
      pg_catalog.pg_roles
    WHERE
      rolname = 'authenticated') THEN
  REVOKE ALL ON public.google_oauth FROM authenticated;
END IF;
END
$$;
