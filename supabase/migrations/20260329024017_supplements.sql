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
  time_blocks text[] NOT NULL CHECK (time_blocks <@ ARRAY['morning', 'lunch', 'evening', 'any'] AND array_length(time_blocks, 1) > 0),
  dosage text NOT NULL,
  frequency text NOT NULL,
  started_at date NOT NULL DEFAULT CURRENT_DATE,
  ended_at date,
  end_reason text,
  replaces_id integer REFERENCES supplement.log(id),
  replacement_reason text,
  CHECK (ended_at IS NULL OR ended_at >= started_at),
  CHECK ((ended_at IS NULL AND end_reason IS NULL) OR (ended_at IS NOT NULL AND end_reason IS NOT NULL)),
  CHECK ((replaces_id IS NULL AND replacement_reason IS NULL) OR (replaces_id IS NOT NULL AND replacement_reason IS NOT NULL))
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

CREATE FUNCTION supplement.immutable_closed_row()
  RETURNS TRIGGER
  AS $$
BEGIN
  IF OLD.ended_at IS NOT NULL THEN
    RAISE EXCEPTION 'Cannot modify a closed log entry';
  END IF;
  RETURN NEW;
END;
$$
LANGUAGE plpgsql;

CREATE TRIGGER immutable_closed
  BEFORE UPDATE ON supplement.log
  FOR EACH ROW
  EXECUTE FUNCTION supplement.immutable_closed_row();

CREATE FUNCTION supplement.require_replacement_chain()
  RETURNS TRIGGER
  AS $$
BEGIN
  IF NEW.replaces_id IS NOT NULL THEN
    IF NOT EXISTS(
      SELECT
        1
      FROM
        supplement.log
      WHERE
        id = NEW.replaces_id
        AND inventory_id = NEW.inventory_id
        AND ended_at IS NOT NULL) THEN
    RAISE EXCEPTION 'replaces_id must reference a closed log entry for the same supplement';
  END IF;
ELSIF EXISTS(
    SELECT
      1
    FROM
      supplement.log
    WHERE
      user_id = NEW.user_id
      AND inventory_id = NEW.inventory_id) THEN
  RAISE EXCEPTION 'A log entry already exists for this supplement — replaces_id and replacement_reason are required';
END IF;
  RETURN NEW;
END;
$$
LANGUAGE plpgsql;

CREATE TRIGGER require_chain
  BEFORE INSERT ON supplement.log
  FOR EACH ROW
  EXECUTE FUNCTION supplement.require_replacement_chain();

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
