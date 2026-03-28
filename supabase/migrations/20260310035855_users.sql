-- Copyright 2026 Alex Zaitsev
-- SPDX-License-Identifier: AGPL-3.0-only

CREATE SCHEMA person;

GRANT USAGE ON SCHEMA person TO app_user;

ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA person
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO app_user;

CREATE TABLE person.users (
    id            TEXT PRIMARY KEY,
    google_email  TEXT UNIQUE NOT NULL,
    display_name  TEXT NOT NULL,
    sex           TEXT CHECK (sex IN ('m', 'f')) NOT NULL,
    date_of_birth DATE NOT NULL
);

ALTER TABLE person.users ENABLE ROW LEVEL SECURITY;

CREATE POLICY users_select ON person.users FOR SELECT
  USING (id = current_setting('app.current_user_id', true));
CREATE POLICY users_modify ON person.users FOR UPDATE
  USING (id = current_setting('app.current_user_id', true))
  WITH CHECK (id = current_setting('app.current_user_id', true));

CREATE TABLE person.health_profiles (
    user_id             TEXT PRIMARY KEY REFERENCES person.users(id) ON DELETE CASCADE,
    conditions          JSONB DEFAULT '[]'::jsonb CHECK (jsonb_typeof(conditions) = 'array'),
    family_history      JSONB DEFAULT '[]'::jsonb CHECK (jsonb_typeof(family_history) = 'array'),
    substances          JSONB DEFAULT '[]'::jsonb CHECK (jsonb_typeof(substances) = 'array'),
    diet_notes          TEXT,
    activity_notes      TEXT,
    safety_checks       JSONB DEFAULT '[]'::jsonb CHECK (jsonb_typeof(safety_checks) = 'array'),
    methodology_notes   TEXT,
    health_priorities   JSONB DEFAULT '[]'::jsonb CHECK (jsonb_typeof(health_priorities) = 'array')
);

ALTER TABLE person.health_profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY user_isolation ON person.health_profiles
  FOR ALL
  USING (user_id = current_setting('app.current_user_id', true))
  WITH CHECK (user_id = current_setting('app.current_user_id', true));

CREATE TABLE person.preferences (
    user_id             TEXT PRIMARY KEY REFERENCES person.users(id) ON DELETE CASCADE,
    location            TEXT,                                  -- city, region, country
    occupation          TEXT,
    language            TEXT NOT NULL DEFAULT 'en' CHECK (language ~ '^[a-z]{2}$'),
    units               TEXT NOT NULL DEFAULT 'metric' CHECK (units IN ('metric', 'imperial')),
    currency            TEXT NOT NULL DEFAULT 'USD' CHECK (currency ~ '^[A-Z]{3}$'),
    date_format         TEXT NOT NULL DEFAULT 'YYYY-MM-DD' CHECK (date_format IN ('YYYY-MM-DD', 'DD/MM/YYYY', 'MM/DD/YYYY', 'DD.MM.YYYY', 'YYYY/MM/DD', 'MM-DD-YYYY', 'DD-MM-YYYY')),
    communication       TEXT
);

ALTER TABLE person.preferences ENABLE ROW LEVEL SECURITY;

CREATE POLICY user_isolation ON person.preferences
  FOR ALL
  USING (user_id = current_setting('app.current_user_id', true))
  WITH CHECK (user_id = current_setting('app.current_user_id', true));
