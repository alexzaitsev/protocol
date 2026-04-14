---
title: Schema
description: Tables, schemas, and the SCD Type 2 shape of the supplement journal.
---

Protocol uses three PostgreSQL schemas:

- **`person`** - user identity, health profile, preferences (one row per user)
- **`supplements`** - shared inventory plus a per-user journal and context
- **`public`** - OAuth token storage only (not user-facing data)

All migrations live in `supabase/migrations/` and are applied by the `deploy` workflow.

## `person` schema

Per-user demographics and profile data. Every table here is user-scoped with RLS enabled.

### `person.users`

The canonical identity record. One row per human.

| Column | Type | Notes |
|--------|------|-------|
| `id` | `text` PK | Short slug (`john`, `jane`). **Not** a UUID - intentionally human-readable |
| `google_email` | `text` UNIQUE | Must match the Google account used at OAuth sign-in |
| `display_name` | `text` | Shown in LLM responses |
| `sex` | `text` | `'m'` or `'f'` (enforced by CHECK) - drives sex-specific lab reference ranges |
| `date_of_birth` | `date` | Used for age-gated recommendations |

### `person.health_profiles`

One row per user (`user_id` is both PK and FK to `person.users` with `ON DELETE CASCADE`). All list-shaped fields are `jsonb` arrays validated by CHECK constraints and Pydantic on read.

| Column | Type | Purpose |
|--------|------|---------|
| `conditions` | `jsonb[]` | Current medical conditions `[{name, status, notes}]` |
| `family_history` | `jsonb[]` | Hereditary risks `[{condition, relative}]` |
| `substances` | `jsonb[]` | Caffeine / alcohol / other `[{name, frequency, notes}]` |
| `diet_notes` | `text` | Free-form eating patterns |
| `activity_notes` | `text` | Free-form exercise notes |
| `safety_checks` | `jsonb[]` | Topics the LLM must verify before recommending |
| `methodology_notes` | `text` | Preferred health framework |
| `health_priorities` | `jsonb[]` | Ranked goals |

### `person.preferences`

One row per user - locale, units, and communication style.

| Column | Default | Constraint |
|--------|---------|------------|
| `language` | `'en'` | ISO 639-1 (two lowercase letters) |
| `units` | `'metric'` | `metric` or `imperial` |
| `currency` | `'USD'` | ISO 4217 (three uppercase letters) |
| `date_format` | `'YYYY-MM-DD'` | One of seven allowed patterns |
| `location` | - | Free-form text - city, region, country |
| `occupation` | - | Free-form text - user's job or profession |
| `communication` | - | Free-form text - communication style |

## `supplements` schema

### `supplements.inventory`

Shared across all users. A single household keeps one catalog so that two family members on the same "Jamieson Vitamin D3 1000 IU" can reference the same `inventory_id`. No RLS - reads are broadly allowed; writes go through MCP tools.

| Column | Type | Notes |
|--------|------|-------|
| `id` | `integer` PK | Generated identity |
| `name` | `text` | - |
| `brand` | `text` | - |
| `category` | `text` | e.g. vitamin, mineral, herb |
| `form` | `text` | e.g. capsule, softgel, powder |
| `dosage_per_unit` | `text` | e.g. "500 mg", "1000 IU" |
| `features` | `text[]` | Optional tags, e.g. `{timed release,micronized}`. Default `{}` |
| `url` | `text` | Optional product URL |

`UNIQUE (name, brand)` prevents duplicate catalog entries.

### `supplements.journal` - SCD Type 2

The core protocol history. Every regimen change **closes** a row (sets `ended_at`) and **opens** a new one linking back via `replaces_id`. This is what lets you reconstruct the exact protocol on any past date.

| Column | Type | Notes |
|--------|------|-------|
| `id` | `integer` PK | Generated identity |
| `user_id` | `text` | FK to `person.users(id)` ON DELETE CASCADE |
| `inventory_id` | `integer` | FK to `supplements.inventory(id)` |
| `time_blocks` | `text[]` | Non-empty subset of `{morning, lunch, evening, any}` |
| `dosage` | `text` | Free-form, e.g. "500 mg" |
| `frequency` | `text` | Free-form, e.g. "twice daily" |
| `started_at` | `date` | Defaults to `CURRENT_DATE` |
| `replaces_id` | `integer` | FK to `supplements.journal(id)`. `NULL` for first entries |
| `replacement_reason` | `text` | Required when `replaces_id` is set |
| `ended_at` | `date` | `NULL` means active |
| `end_reason` | `text` | Optional, requires `ended_at` |

Invariants enforced by CHECK constraints and triggers:

- `ended_at >= started_at` if present
- `end_reason` requires `ended_at`
- `replaces_id` and `replacement_reason` are both-or-neither
- **Unique active entry per user+supplement** - partial unique index `(user_id, inventory_id) WHERE ended_at IS NULL` prevents two concurrent rows for the same thing
- **Closed rows are immutable** - `immutable_closed` trigger rejects any UPDATE on a row where `ended_at IS NOT NULL`
- **Replacement chain integrity** - `require_chain` trigger enforces that `replaces_id` points to a closed row for the same `inventory_id`, and that you cannot insert a second "first" entry for a supplement that already has history

### `supplements.context`

One row per `(user_id, inventory_id)` - the **purpose** the user takes this supplement for. Separate from `journal` because purpose rarely changes while dosage and timing do.

| Column | Type | Notes |
|--------|------|-------|
| `id` | `integer` PK | Generated identity |
| `user_id` | `text` | FK to `person.users(id)` ON DELETE CASCADE |
| `inventory_id` | `integer` | FK to `supplements.inventory(id)` |
| `purpose` | `text[]` | Non-empty array, e.g. `{bone health,immune support}` |

`UNIQUE (user_id, inventory_id)` - one context entry per user per supplement.

## `public.google_oauth`

Backing store for FastMCP's OAuth flow (access tokens, refresh tokens, PKCE state). RLS is enabled but no policies are defined - only the `postgres` superuser (the MCP server itself) should ever read this table. `anon` and `authenticated` roles are explicitly revoked in the migration.

| Column | Type | Notes |
|--------|------|-------|
| `collection` | `text` | Part of composite PK - groups token records by type |
| `key` | `text` | Part of composite PK - identifies the specific token |
| `value` | `jsonb` | Token payload |
| `ttl` | `double precision` | Time-to-live in seconds |
| `created_at` | `timestamptz` | - |
| `expires_at` | `timestamptz` | Indexed for expiry lookups |
