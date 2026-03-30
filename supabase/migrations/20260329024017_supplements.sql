-- Copyright 2026 Alex Zaitsev
-- SPDX-License-Identifier: AGPL-3.0-only
CREATE SCHEMA supplement;

GRANT USAGE ON SCHEMA supplement TO app_user;

CREATE TABLE supplement.inventory(
  id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  name text NOT NULL,
  brand text NOT NULL,
  category text NOT NULL,
  form text NOT NULL,
  dosage_per_unit text NOT NULL,
  features text[] NOT NULL DEFAULT '{}',
  url text,
  UNIQUE (name, brand)
);

GRANT SELECT, INSERT, UPDATE ON supplement.inventory TO app_user;

CREATE INDEX idx_inventory_name_lower ON supplement.inventory(lower(name));

CREATE TABLE supplement.log (
  id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  user_id text NOT NULL REFERENCES person.users(id) ON DELETE CASCADE,
  inventory_id integer NOT NULL REFERENCES supplement.inventory(id),
  time_blocks text[] NOT NULL CHECK (time_blocks <@ ARRAY['morning',
    'lunch', 'evening', 'any'] AND
    array_length(time_blocks, 1) > 0),
  dosage text NOT NULL,
  frequency text NOT NULL,
  started_at date NOT NULL DEFAULT CURRENT_DATE,
  ended_at date,
  replaces_id integer REFERENCES supplement.log(id),
  replacement_reason text,
  CHECK (ended_at IS NULL OR ended_at >= started_at),
  CHECK ((replaces_id IS NULL AND replacement_reason IS NULL) OR (replaces_id
    IS NOT NULL AND replacement_reason IS NOT NULL))
);

GRANT SELECT, INSERT, UPDATE ON supplement.log TO app_user;

ALTER TABLE supplement.log ENABLE ROW LEVEL SECURITY;

CREATE POLICY user_isolation ON supplement.log
  FOR ALL
    USING (user_id = current_setting('app.current_user_id', TRUE))
    WITH CHECK (user_id = current_setting('app.current_user_id', TRUE));

CREATE INDEX idx_log_user_active ON supplement.log(user_id, ended_at);

CREATE INDEX idx_log_replaces ON supplement.log(replaces_id)
WHERE
  replaces_id IS NOT NULL;

CREATE UNIQUE INDEX idx_log_one_active ON supplement.log(user_id, inventory_id)
WHERE
  ended_at IS NULL;

CREATE INDEX idx_log_inventory ON supplement.log(inventory_id);

CREATE TABLE supplement.context(
  id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  user_id text NOT NULL REFERENCES person.users(id) ON DELETE CASCADE,
  inventory_id integer NOT NULL REFERENCES supplement.inventory(id),
  purpose text[] NOT NULL CHECK (array_length(purpose, 1) > 0),
  UNIQUE (user_id, inventory_id)
);

GRANT SELECT, INSERT, UPDATE ON supplement.context TO app_user;

ALTER TABLE supplement.context ENABLE ROW LEVEL SECURITY;

CREATE POLICY user_isolation ON supplement.context
  FOR ALL
    USING (user_id = current_setting('app.current_user_id', TRUE))
    WITH CHECK (user_id = current_setting('app.current_user_id', TRUE));

CREATE INDEX idx_context_inventory ON supplement.context(inventory_id);

GRANT USAGE ON ALL SEQUENCES IN SCHEMA supplement TO app_user;
