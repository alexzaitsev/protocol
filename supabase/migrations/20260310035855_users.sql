-- Copyright 2026 Alex Zaitsev
-- SPDX-License-Identifier: AGPL-3.0-only
CREATE SCHEMA person;

GRANT USAGE ON SCHEMA person TO app_user;

ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA person GRANT
SELECT
, INSERT, UPDATE, DELETE ON TABLES TO app_user;

CREATE TABLE person.users(
  id text PRIMARY KEY,
  google_email text UNIQUE NOT NULL,
  display_name text NOT NULL,
  sex text CHECK (sex IN ('m', 'f')) NOT NULL,
  date_of_birth date NOT NULL
);

ALTER TABLE person.users ENABLE ROW LEVEL SECURITY;

CREATE POLICY users_select ON person.users
  FOR SELECT
    USING (id = current_setting('app.current_user_id', TRUE));

CREATE POLICY users_modify ON person.users
  FOR UPDATE
    USING (id = current_setting('app.current_user_id', TRUE))
    WITH CHECK (id = current_setting('app.current_user_id', TRUE));

CREATE TABLE person.health_profiles(
  user_id text PRIMARY KEY REFERENCES person.users(id) ON DELETE CASCADE,
  conditions jsonb DEFAULT '[]'::jsonb CHECK
    (jsonb_typeof(conditions) = 'array'),
  family_history jsonb DEFAULT '[]'::jsonb CHECK
    (jsonb_typeof(family_history) = 'array'),
  substances jsonb DEFAULT '[]'::jsonb CHECK
    (jsonb_typeof(substances) = 'array'),
  diet_notes text,
  activity_notes text,
  safety_checks jsonb DEFAULT '[]'::jsonb CHECK
    (jsonb_typeof(safety_checks) = 'array'),
  methodology_notes text,
  health_priorities jsonb DEFAULT '[]'::jsonb CHECK
    (jsonb_typeof(health_priorities) = 'array')
);

ALTER TABLE person.health_profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY user_isolation ON person.health_profiles
  FOR ALL
    USING (user_id = current_setting('app.current_user_id', TRUE))
    WITH CHECK (user_id = current_setting('app.current_user_id', TRUE));

CREATE TABLE person.preferences(
  user_id text PRIMARY KEY REFERENCES person.users(id) ON DELETE CASCADE,
  location text, -- city, region, country
  occupation text,
  "language" text NOT NULL DEFAULT 'en' CHECK ("language" ~ '^[a-z]{2}$'),
  units text NOT NULL DEFAULT 'metric' CHECK (units IN ('metric',
    'imperial')),
  currency text NOT NULL DEFAULT 'USD' CHECK (currency ~ '^[A-Z]{3}$'),
  date_format text NOT NULL DEFAULT 'YYYY-MM-DD' CHECK (date_format IN
    ('YYYY-MM-DD', 'DD/MM/YYYY', 'MM/DD/YYYY', 'DD.MM.YYYY',
    'YYYY/MM/DD', 'MM-DD-YYYY', 'DD-MM-YYYY')),
  communication text
);

ALTER TABLE person.preferences ENABLE ROW LEVEL SECURITY;

CREATE POLICY user_isolation ON person.preferences
  FOR ALL
    USING (user_id = current_setting('app.current_user_id', TRUE))
    WITH CHECK (user_id = current_setting('app.current_user_id', TRUE));
