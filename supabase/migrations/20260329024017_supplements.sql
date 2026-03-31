-- Copyright 2026 Alex Zaitsev
-- SPDX-License-Identifier: AGPL-3.0-only
CREATE SCHEMA supplements;

GRANT USAGE ON SCHEMA supplements TO app_user;

CREATE TABLE supplements.inventory(
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

GRANT SELECT, INSERT, UPDATE ON supplements.inventory TO app_user;

CREATE INDEX idx_inventory_name_lower ON supplements.inventory(lower(name));

CREATE TABLE supplements.journal(
  id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  user_id text NOT NULL REFERENCES person.users(id) ON DELETE CASCADE,
  inventory_id integer NOT NULL REFERENCES supplements.inventory(id),
  time_blocks text[] NOT NULL CHECK (time_blocks <@ ARRAY['morning', 'lunch', 'evening', 'any'] AND array_length(time_blocks, 1) > 0),
  dosage text NOT NULL,
  frequency text NOT NULL,
  started_at date NOT NULL DEFAULT CURRENT_DATE,
  replaces_id integer REFERENCES supplements.journal(id),
  replacement_reason text,
  ended_at date,
  end_reason text,
  CHECK (ended_at IS NULL OR ended_at >= started_at),
  CHECK (end_reason IS NULL OR ended_at IS NOT NULL),
  CHECK ((replaces_id IS NULL AND replacement_reason IS NULL) OR (replaces_id IS NOT NULL AND replacement_reason IS NOT NULL))
);

GRANT SELECT, INSERT, UPDATE ON supplements.journal TO app_user;

ALTER TABLE supplements.journal ENABLE ROW LEVEL SECURITY;

CREATE POLICY user_isolation ON supplements.journal
  FOR ALL
    USING (user_id = current_setting('app.current_user_id', TRUE))
    WITH CHECK (user_id = current_setting('app.current_user_id', TRUE));

CREATE INDEX idx_journal_user_active ON supplements.journal(user_id, ended_at);

CREATE INDEX idx_journal_replaces ON supplements.journal(replaces_id)
WHERE
  replaces_id IS NOT NULL;

CREATE UNIQUE INDEX idx_journal_one_active ON supplements.journal(user_id, inventory_id)
WHERE
  ended_at IS NULL;

CREATE INDEX idx_journal_inventory ON supplements.journal(inventory_id);

CREATE FUNCTION supplements.immutable_closed_row()
  RETURNS TRIGGER
  AS $$
BEGIN
  IF OLD.ended_at IS NOT NULL THEN
    RAISE EXCEPTION 'Cannot modify a closed journal entry';
  END IF;
  RETURN NEW;
END;
$$
LANGUAGE plpgsql;

CREATE TRIGGER immutable_closed
  BEFORE UPDATE ON supplements.journal
  FOR EACH ROW
  EXECUTE FUNCTION supplements.immutable_closed_row();

CREATE FUNCTION supplements.require_replacement_chain()
  RETURNS TRIGGER
  AS $$
BEGIN
  IF NEW.replaces_id IS NOT NULL THEN
    IF NOT EXISTS(
      SELECT
        1
      FROM
        supplements.journal
      WHERE
        id = NEW.replaces_id
        AND inventory_id = NEW.inventory_id
        AND ended_at IS NOT NULL) THEN
    RAISE EXCEPTION 'replaces_id must reference a closed journal entry for the same supplement';
  END IF;
ELSIF EXISTS(
    SELECT
      1
    FROM
      supplements.journal
    WHERE
      user_id = NEW.user_id
      AND inventory_id = NEW.inventory_id) THEN
  RAISE EXCEPTION 'A journal entry already exists for this supplement — replaces_id and replacement_reason are required';
END IF;
  RETURN NEW;
END;
$$
LANGUAGE plpgsql;

CREATE TRIGGER require_chain
  BEFORE INSERT ON supplements.journal
  FOR EACH ROW
  EXECUTE FUNCTION supplements.require_replacement_chain();

CREATE TABLE supplements.context(
  id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  user_id text NOT NULL REFERENCES person.users(id) ON DELETE CASCADE,
  inventory_id integer NOT NULL REFERENCES supplements.inventory(id),
  purpose text[] NOT NULL CHECK (array_length(purpose, 1) > 0),
  UNIQUE (user_id, inventory_id)
);

GRANT SELECT, INSERT, UPDATE ON supplements.context TO app_user;

ALTER TABLE supplements.context ENABLE ROW LEVEL SECURITY;

CREATE POLICY user_isolation ON supplements.context
  FOR ALL
    USING (user_id = current_setting('app.current_user_id', TRUE))
    WITH CHECK (user_id = current_setting('app.current_user_id', TRUE));

CREATE INDEX idx_context_inventory ON supplements.context(inventory_id);

GRANT USAGE ON ALL SEQUENCES IN SCHEMA supplements TO app_user;
