---
title: Data Layer
description: How the MCP server talks to PostgreSQL - pool setup and the two access patterns.
---

The server uses [asyncpg](https://magicstack.github.io/asyncpg/) directly - no ORM, no `supabase-py`. All queries are raw SQL with `$1` positional parameters. The pool and helpers live in `server/data/db.py`.

## Connection pool

A single `asyncpg.Pool` is created on startup and closed on shutdown (FastMCP lifespan hook in `app.py`). Configuration:

- `min_size=1`, `max_size=3` - keeps Fly.io memory pressure low while tolerating bursts
- `statement_cache_size=0` - **required** for the Supabase transaction pooler (port `6543`), which rewrites connections between queries and would otherwise poison the cache
- `init=_init_connection` - registers a JSONB codec so `jsonb` columns round-trip through `json.dumps` / `json.loads`

If pool creation fails at boot, the error is logged and retry happens on the next request - this avoids hard-crashing the server when Supabase is briefly unreachable.

## Two access patterns

Every query goes through one of two sets of helpers depending on whether the data is user-scoped.

### Direct access - `postgres` superuser

```python
await execute(sql, *args)
await fetchrow(sql, *args)
await fetch(sql, *args)
```

These run as the pool's default role (`postgres`), bypassing RLS. Use them for:

- Shared lookup tables that aren't keyed by user (e.g. `supplements.inventory`)
- Resolving the authenticated OAuth email → `user_id` slug (`SELECT id FROM person.users WHERE google_email = $1`)
- System-level tables with no RLS policies (e.g. `public.google_oauth` token storage)

### RLS-scoped access - `app_user` role

```python
await execute_rls(sql, *args)
await fetchrow_rls(sql, *args)
await fetch_rls(sql, *args)
```

Each call opens a transaction, switches to the `app_user` role, sets `app.current_user_id`, then runs the query:

```sql
SET LOCAL ROLE app_user;
SELECT set_config('app.current_user_id', $1, true);
-- your query runs here
```

Why `SET LOCAL` (not `SET`): connections return to the pool after the transaction; `SET LOCAL` is automatically reverted at commit, so the next borrower of this connection starts clean. Plain `SET` would leak role and user context across borrowers - a critical isolation bug.

The user ID comes from the OAuth access token's `email` claim (via `fastmcp.server.dependencies.get_access_token()`), looked up once per request against `person.users`. All subsequent RLS queries in the same request reuse that slug.

## What this buys you

- **Defense in depth.** Even if a tool forgets to filter by `user_id`, RLS policies in the database reject cross-user reads and writes. The application layer cannot opt out of enforcement short of intentionally using the direct-access helpers.
- **Single source of truth for authorization.** Per-table `CREATE POLICY` statements in migrations are the authoritative rules. There is no parallel "authz layer" in Python that can drift.
- **Transaction pooler compatibility.** `SET LOCAL` inside an explicit transaction is the only pattern that survives pgbouncer in transaction mode.
