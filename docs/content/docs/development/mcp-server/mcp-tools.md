---
title: MCP Tools
description: Catalog of MCP tools exposed by the Protocol server.
---

The Protocol server exposes a set of MCP tools that an AI assistant calls on the user's behalf. Every tool is either a **read** (annotated `READ` - safe, idempotent) or a **write** (annotated `WRITE` - mutates data). All calls are authenticated via OAuth and scoped to the signed-in user through RLS.

Schemas are derived from Pydantic models in `server/features/` and enforced at the MCP protocol boundary - the LLM sees typed parameters, not free-form text.

## User

Source: `server/features/user.py`

| Tool | Kind | Description |
|------|------|-------------|
| `get_user_profile` | read | Basic demographics - name, sex, date of birth |
| `get_user_health_profile` | read | Conditions, family history, substances, diet, activity, methodology, priorities |
| `update_user_health_profile` | write | Partial update of any health-profile field (omitted fields preserved) |
| `get_user_preferences` | read | Locale, units, currency, date format, communication style |
| `update_user_preferences` | write | Partial update of any preference (omitted fields preserved) |
| `get_user_context` | read | Profile + health profile + preferences in a single joined call - prefer this for session warm-up |

## Supplement inventory

Source: `server/features/supplements.py`. Inventory is **shared across the household** - one catalog, not per user. IDs resolved here are passed into journal / context tools below.

| Tool | Kind | Description |
|------|------|-------------|
| `get_inventory_list` | read | List every item in the shared catalog. Call first to resolve `inventory_id` |
| `get_inventory` | read | Full details for a single inventory item by ID |
| `add_inventory` | write | Add a new supplement to the catalog. Check the list first to avoid `(name, brand)` conflicts |
| `update_inventory` | write | Partial update of catalog fields |

## Supplement journal

The SCD Type 2 history of what the user is taking. Every regimen change closes one row and opens another, linked via `replaces_id` - see [Schema](/development/database/schema/).

| Tool | Kind | Description |
|------|------|-------------|
| `get_supplement_protocol` | read | All currently active supplements - the full active protocol with dosages, schedules, and purpose |
| `get_supplement` | read | Current entry for a given `inventory_id` (or the most recent if none active) |
| `get_supplement_history` | read | Full chronological history for a supplement - every entry, oldest first |
| `add_supplement` | write | Start taking a supplement. Requires `replaces_id` + `replacement_reason` if the user has prior history for this item |
| `update_supplement_replace` | write | Change dosage / frequency / time blocks. Closes the current entry (optional `ended_at`, defaults to today) and opens a new one (optional `started_at`, defaults to today) via SCD Type 2 |
| `update_supplement_end` | write | Stop taking a supplement without a replacement - sets `ended_at` to today |

## Supplement context

Why the user takes a given supplement. Separate from the journal because purpose changes rarely while dosage / timing change often.

| Tool | Kind | Description |
|------|------|-------------|
| `add_context` | write | Attach a purpose list (`['bone health', 'immune support']`) to a user+supplement pair. One context entry per pair |
| `update_context` | write | Replace the purpose list for an existing context entry |

## Read vs write annotations

Tools tagged `READ` are annotated as safe and idempotent - MCP clients may call them speculatively, cache results, or use them for context pre-loading. Tools tagged `WRITE` will not be called without user confirmation in well-behaved clients. The annotations are applied via the `READ` / `WRITE` constants in `server/utils/mcp_annotations.py`.
