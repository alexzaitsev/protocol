-- Copyright 2026 Alex Zaitsev
-- SPDX-License-Identifier: AGPL-3.0-only

CREATE SCHEMA supplement;

GRANT USAGE ON SCHEMA supplement TO app_user;

CREATE TABLE supplement.inventory (
    id               INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name             TEXT NOT NULL,
    brand            TEXT NOT NULL,
    category         TEXT NOT NULL,
    form             TEXT NOT NULL,                                                                -- capsule, powder, liquid, etc.
    dosage_per_unit  TEXT NOT NULL,                                                                -- "500mg", "1000 IU"
    features         JSONB NOT NULL DEFAULT '[]'::jsonb CHECK (jsonb_typeof(features) = 'array'),  -- ["timed release", "quick dissolve"]
    url              TEXT,                                                                         -- URL where to buy
    UNIQUE NULLS NOT DISTINCT (name, brand)
);

GRANT SELECT, INSERT, UPDATE ON supplement.inventory TO app_user;

CREATE INDEX idx_inventory_name_lower ON supplement.inventory (lower(name));

CREATE TABLE supplement.supplements (
    id           INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id      TEXT NOT NULL REFERENCES person.users(id) ON DELETE CASCADE,
    inventory_id INTEGER NOT NULL REFERENCES supplement.inventory(id),
    time_blocks  JSONB NOT NULL CHECK (
        time_blocks <@ '["morning", "lunch", "evening", "any"]'::jsonb
        AND jsonb_array_length(time_blocks) > 0
    ),
    dosage       TEXT NOT NULL,
    frequency    TEXT NOT NULL,
    started_at   DATE NOT NULL DEFAULT CURRENT_DATE,
    ended_at     DATE,
    replaces_id  INTEGER REFERENCES supplement.supplements(id),
    CHECK (ended_at IS NULL OR ended_at >= started_at)
);

GRANT SELECT, INSERT, UPDATE ON supplement.supplements TO app_user;

GRANT USAGE ON ALL SEQUENCES IN SCHEMA supplement TO app_user;

ALTER TABLE supplement.supplements ENABLE ROW LEVEL SECURITY;

CREATE POLICY user_isolation ON supplement.supplements
  FOR ALL
  USING (user_id = current_setting('app.current_user_id', true))
  WITH CHECK (user_id = current_setting('app.current_user_id', true));

CREATE INDEX idx_supplements_user_active ON supplement.supplements (user_id, ended_at);
CREATE INDEX idx_supplements_replaces ON supplement.supplements (replaces_id) WHERE replaces_id IS NOT NULL;
CREATE UNIQUE INDEX idx_supplements_one_active ON supplement.supplements (user_id, inventory_id) WHERE ended_at IS NULL;
