---
title: RLS Policies
description: How Row-Level Security enforces per-user isolation at the database level.
---

Protocol relies on PostgreSQL Row-Level Security (RLS) - not application code - as the final authority on who can read and write which rows. If a tool forgets to filter by `user_id`, the database rejects the query anyway.

## The `app_user` role

A single NOLOGIN role called `app_user` is the only identity the application ever runs user-scoped queries as. It's created in the first migration (`20260310030000_role.sql`) and granted to `postgres` so the pool can switch into it transactionally:

```sql
CREATE ROLE app_user NOLOGIN;
GRANT app_user TO postgres;
```

Per-schema privileges are granted explicitly (`GRANT USAGE ON SCHEMA person TO app_user`, etc.) so that new tables created by the `postgres` user don't silently become accessible - the migration must opt each table in.

## The `app.current_user_id` session variable

RLS policies compare row ownership to a custom GUC (Grand Unified Configuration) parameter, `app.current_user_id`, which the server sets at the start of every scoped transaction:

```sql
SET LOCAL ROLE app_user;
SELECT set_config('app.current_user_id', $1, true);
```

The `true` third argument to `set_config` makes it transaction-local - exactly like `SET LOCAL`. When the transaction commits or rolls back, both the role and the GUC revert, so connections return to the pool clean. This is critical under the Supabase transaction pooler, where every connection handoff must leave no residual session state.

## Per-table policies

Every user-owned table follows the same shape: RLS enabled, one `user_isolation` policy covering all operations.

```sql
ALTER TABLE person.health_profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY user_isolation ON person.health_profiles
  FOR ALL
  USING      (user_id = current_setting('app.current_user_id', TRUE))
  WITH CHECK (user_id = current_setting('app.current_user_id', TRUE));
```

- **`USING`** - filters rows visible to `SELECT`, `UPDATE`, `DELETE`
- **`WITH CHECK`** - rejects `INSERT` or `UPDATE` that would produce a row the caller cannot see
- The second argument to `current_setting(..., TRUE)` returns NULL instead of raising if the GUC is unset - so a bare connection that forgot to call `set_config` sees zero rows rather than an error

`person.users` is slightly different: it keys on `id` (not `user_id`) and only exposes `SELECT` and `UPDATE` via policy - identity rows are provisioned manually in the SQL Editor, not by the MCP server.

## Tables with RLS enabled

| Table | Policy name | Key column |
|-------|-------------|------------|
| `person.users` | `users_select`, `users_modify` | `id` |
| `person.health_profiles` | `user_isolation` | `user_id` |
| `person.preferences` | `user_isolation` | `user_id` |
| `supplements.journal` | `user_isolation` | `user_id` |
| `supplements.context` | `user_isolation` | `user_id` |
| `public.google_oauth` | - *(no policies; superuser-only)* | - |

`supplements.inventory` is deliberately **not** under RLS - the catalog is shared across the household.

## What RLS does not cover

RLS checks row ownership but does not validate the shape of data. Application-level constraints (CHECK, UNIQUE, triggers - see [Schema](/development/database/schema/)) handle things like "you can only have one active entry per supplement" or "closed journal rows are immutable." The two layers are complementary.
