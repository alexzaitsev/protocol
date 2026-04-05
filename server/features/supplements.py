# Copyright 2026 Alex Zaitsev
# SPDX-License-Identifier: AGPL-3.0-only

import json
from datetime import date
from enum import StrEnum

import asyncpg
from app import mcp
from data.db import fetch, fetch_rls, fetchrow, fetchrow_rls
from pydantic import BaseModel, Field
from utils.db import build_update_where
from utils.mcp_annotations import READ, WRITE
from utils.pydantic import describe_schema


class InventoryItem(BaseModel):
    id: int
    name: str
    brand: str
    category: str = Field(
        description="e.g. vitamin, mineral, amino acid, fatty acid, fiber, probiotic"
    )
    form: str = Field(description="e.g. capsule, tablet, powder, softgel, liquid drop")
    dosage_per_unit: str = Field(
        description="amount per single unit/scoop, e.g. '1000 mg', '5 g', '10 billion CFU'"
    )
    features: list[str] = Field(
        description="notable product traits, e.g. 'timed release', 'micronized'"
    )
    url: str | None = Field(description="product URL")


class TimeBlock(StrEnum):
    morning = "morning"
    lunch = "lunch"
    evening = "evening"
    any = "any"


class JournalEntry(BaseModel):
    id: int
    inventory: InventoryItem
    time_blocks: list[TimeBlock]
    dosage: str
    frequency: str
    started_at: date
    replaces_id: int | None
    replacement_reason: str | None
    ended_at: date | None
    end_reason: str | None
    purpose: list[str] | None = None


class Context(BaseModel):
    id: int
    inventory_id: int
    purpose: list[str] = Field(
        description="why the user takes this supplement, e.g. ['bone health', 'immune support']"
    )


def _build_journal_entry(row: asyncpg.Record) -> JournalEntry:
    r = dict(row)
    return JournalEntry(
        id=r["id"],
        inventory=InventoryItem(
            id=r["inventory_id"],
            name=r["inv_name"],
            brand=r["brand"],
            category=r["category"],
            form=r["form"],
            dosage_per_unit=r["dosage_per_unit"],
            features=r["features"],
            url=r["url"],
        ),
        time_blocks=r["time_blocks"],
        dosage=r["dosage"],
        frequency=r["frequency"],
        started_at=r["started_at"],
        replaces_id=r["replaces_id"],
        replacement_reason=r["replacement_reason"],
        ended_at=r.get("ended_at"),
        end_reason=r.get("end_reason"),
        purpose=r.get("purpose"),
    )


# ---------------------------------------------------------------------------
# Inventory
# ---------------------------------------------------------------------------


@mcp.tool(
    name="lookup_inventory",
    annotations=READ,
    description=(
        "Search the shared supplement inventory by name or brand (case-insensitive). "
        "Returns matching items with IDs. Use this to resolve inventory_id for operations that require it. "
        "Returns [] if no matches — try a shorter or alternative query.\n"
        "Returns array of items.\n"
        f"{describe_schema(InventoryItem)}"
    ),
)
async def lookup_inventory(
    query: str = Field(
        description="search term matched against name and brand (e.g. 'D3', 'Jamieson')"
    ),
) -> str:
    rows = await fetch(
        """
        SELECT
          *
        FROM
          supplements.inventory
        WHERE
          name ILIKE '%' || $1 || '%'
          OR brand ILIKE '%' || $1 || '%'
        ORDER BY
          name
        """,
        query,
    )
    items = [InventoryItem(**dict(r)).model_dump(mode="json") for r in rows]
    return json.dumps(items)


@mcp.tool(
    name="add_inventory",
    annotations=WRITE,
    description=(
        "Add a new supplement to the shared inventory catalog. "
        "Use lookup_inventory first to avoid duplicates — inventory must be unique. "
        "Returns the created item with its id.\n"
        f"{describe_schema(InventoryItem)}"
    ),
)
async def add_inventory(
    name: str = Field(description="supplement name, e.g. 'Vitamin D3'"),
    brand: str = Field(description="brand name, e.g. 'Jamieson'"),
    category: str = Field(
        description="e.g. vitamin, mineral, amino acid, fatty acid, fiber, probiotic"
    ),
    form: str = Field(description="e.g. capsule, tablet, powder, softgel, liquid drop"),
    dosage_per_unit: str = Field(
        description="amount per single unit/scoop, e.g. '1000 mg', '5 g', '10 billion CFU'"
    ),
    features: list[str] = Field(
        default_factory=list,
        description="notable product traits, e.g. 'timed release', 'micronized'",
    ),
    url: str | None = Field(default=None, description="product URL"),
) -> str:
    try:
        row = await fetchrow(
            """
            INSERT INTO supplements.inventory (name, brand, category, form,
              dosage_per_unit, features, url)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING *
            """,
            name,
            brand,
            category,
            form,
            dosage_per_unit,
            features,
            url,
        )
    except asyncpg.UniqueViolationError:
        return json.dumps(
            {"error": "inventory item with this name and brand already exists"}
        )
    assert row is not None
    return InventoryItem(**dict(row)).model_dump_json()


@mcp.tool(
    name="update_inventory",
    annotations=WRITE,
    description=(
        "Update fields on a shared inventory item by inventory_id. "
        "Only provided fields are changed; omitted fields remain unchanged.\n"
        f"{describe_schema(InventoryItem)}"
    ),
)
async def update_inventory(
    inventory_id: int = Field(
        description="inventory item ID, as returned by lookup_inventory"
    ),
    name: str | None = Field(default=None, description="supplement name"),
    brand: str | None = Field(default=None, description="brand name"),
    category: str | None = Field(
        default=None,
        description="e.g. vitamin, mineral, amino acid, fatty acid, fiber, probiotic",
    ),
    form: str | None = Field(
        default=None,
        description="e.g. capsule, tablet, powder, softgel, liquid drop",
    ),
    dosage_per_unit: str | None = Field(
        default=None,
        description="amount per single unit/scoop, e.g. '1000 mg', '5 g', '10 billion CFU'",
    ),
    features: list[str] | None = Field(
        default=None,
        description="notable product traits, e.g. 'timed release', 'micronized'",
    ),
    url: str | None = Field(default=None, description="product URL"),
) -> str:
    journal_row = await fetchrow_rls(
        "SELECT 1 FROM supplements.journal WHERE inventory_id = $1 LIMIT 1",
        inventory_id,
    )
    if journal_row is None:
        return json.dumps(
            {
                "error": "no journal entries for this inventory_id — you can only update supplements you have taken"
            }
        )
    fields: dict[str, object] = {
        "name": name,
        "brand": brand,
        "category": category,
        "form": form,
        "dosage_per_unit": dosage_per_unit,
        "features": features,
        "url": url,
    }
    query, args = build_update_where(
        "supplements.inventory", fields, {"id": inventory_id}
    )
    if not query:
        return json.dumps({"error": "no fields provided"})
    row = await fetchrow(query, *args)
    if row is None:
        return json.dumps({"error": "inventory item not found"})
    return InventoryItem(**dict(row)).model_dump_json()


# ---------------------------------------------------------------------------
# Context
# ---------------------------------------------------------------------------


@mcp.tool(
    name="add_context",
    annotations=WRITE,
    description=(
        "Add purpose context for a supplement in the user's journal. "
        "Each supplement can have one context entry per user — "
        "use update_context to change an existing one.\n"
        f"{describe_schema(Context)}"
    ),
)
async def add_context(
    inventory_id: int = Field(
        description="inventory item ID, as returned by lookup_inventory"
    ),
    purpose: list[str] = Field(
        description="why the user takes this supplement, e.g. ['bone health', 'immune support']"
    ),
) -> str:
    try:
        row = await fetchrow_rls(
            """
            INSERT INTO supplements.context (user_id, inventory_id, purpose)
            VALUES (current_setting('app.current_user_id', true), $1, $2)
            RETURNING *
            """,
            inventory_id,
            purpose,
        )
    except asyncpg.UniqueViolationError:
        return json.dumps(
            {
                "error": "context already exists for this supplement — use update_context to change it"
            }
        )
    assert row is not None
    return Context(**dict(row)).model_dump_json()


@mcp.tool(
    name="update_context",
    annotations=WRITE,
    description=(
        "Update the purpose context for a supplement. "
        "Replaces the full purpose list.\n"
        f"{describe_schema(Context)}"
    ),
)
async def update_context(
    inventory_id: int = Field(
        description="inventory item ID, as returned by lookup_inventory"
    ),
    purpose: list[str] = Field(
        description="updated purpose list, e.g. ['bone health', 'immune support']"
    ),
) -> str:
    row = await fetchrow_rls(
        """
        UPDATE supplements.context
        SET purpose = $1
        WHERE inventory_id = $2
        RETURNING *
        """,
        purpose,
        inventory_id,
    )
    if row is None:
        return json.dumps(
            {"error": "no context found for this supplement — use add_context first"}
        )
    return Context(**dict(row)).model_dump_json()


# ---------------------------------------------------------------------------
# Protocol
# ---------------------------------------------------------------------------


@mcp.tool(
    name="get_supplement_protocol",
    annotations=READ,
    description=(
        "Get all active supplements the user is currently taking — the full protocol. "
        "Returns dosing schedules, inventory details, and purpose for each supplement. "
        "Ordered by time-block priority (any > morning > lunch > evening), then by name. "
        "Returns [] if no active supplements.\n"
        "Returns array of items.\n"
        f"{describe_schema(JournalEntry)}"
    ),
)
async def get_supplement_protocol() -> str:
    rows = await fetch_rls(
        """
        SELECT
          j.id,
          j.inventory_id,
          j.time_blocks,
          j.dosage,
          j.frequency,
          j.started_at,
          j.replaces_id,
          j.replacement_reason,
          j.ended_at,
          j.end_reason,
          i.name AS inv_name,
          i.brand,
          i.category,
          i.form,
          i.dosage_per_unit,
          i.features,
          i.url,
          c.purpose
        FROM
          supplements.journal j
          JOIN supplements.inventory i ON i.id = j.inventory_id
          LEFT JOIN supplements.context c ON c.inventory_id = j.inventory_id
            AND c.user_id = j.user_id
        WHERE
          j.ended_at IS NULL
        ORDER BY
          CASE
            WHEN 'any' = ANY (j.time_blocks) THEN 0
            WHEN 'morning' = ANY (j.time_blocks) THEN 1
            WHEN 'lunch' = ANY (j.time_blocks) THEN 2
            WHEN 'evening' = ANY (j.time_blocks) THEN 3
          END,
          i.name
        """
    )
    entries = [_build_journal_entry(row) for row in rows]
    return json.dumps([e.model_dump(mode="json") for e in entries])


# ---------------------------------------------------------------------------
# Supplement
# ---------------------------------------------------------------------------


@mcp.tool(
    name="get_supplement",
    annotations=READ,
    description=(
        "Get the current supplement entry by inventory_id. "
        "Returns the active entry, or the most recently ended if none active. "
        "Includes full inventory details and user's purpose.\n"
        f"{describe_schema(JournalEntry)}"
    ),
)
async def get_supplement(
    inventory_id: int = Field(
        description="inventory item ID, as returned by lookup_inventory"
    ),
) -> str:
    row = await fetchrow_rls(
        """
        SELECT
          j.id,
          j.inventory_id,
          j.time_blocks,
          j.dosage,
          j.frequency,
          j.started_at,
          j.replaces_id,
          j.replacement_reason,
          j.ended_at,
          j.end_reason,
          i.name AS inv_name,
          i.brand,
          i.category,
          i.form,
          i.dosage_per_unit,
          i.features,
          i.url,
          c.purpose
        FROM
          supplements.journal j
          JOIN supplements.inventory i ON i.id = j.inventory_id
          LEFT JOIN supplements.context c ON c.inventory_id = j.inventory_id
            AND c.user_id = j.user_id
        WHERE
          j.inventory_id = $1
        ORDER BY
          j.ended_at IS NULL DESC,
          j.ended_at DESC
        LIMIT 1
        """,
        inventory_id,
    )
    if row is None:
        return json.dumps({"error": "no supplement found for this inventory_id"})
    return _build_journal_entry(row).model_dump_json()


@mcp.tool(
    name="get_supplement_history",
    annotations=READ,
    description=(
        "Get the full change history for a supplement by inventory_id. "
        "Returns all journal entries in chronological order (oldest first), "
        "including ended entries and their replacement chains via replaces_id. "
        "Does not include purpose — history tracks regimen changes only. "
        "Returns [] if no entries found.\n"
        "Returns array of items.\n"
        f"{describe_schema(JournalEntry)}"
    ),
)
async def get_supplement_history(
    inventory_id: int = Field(
        description="inventory item ID, as returned by lookup_inventory"
    ),
) -> str:
    rows = await fetch_rls(
        """
        SELECT
          j.id,
          j.inventory_id,
          j.time_blocks,
          j.dosage,
          j.frequency,
          j.started_at,
          j.replaces_id,
          j.replacement_reason,
          j.ended_at,
          j.end_reason,
          i.name AS inv_name,
          i.brand,
          i.category,
          i.form,
          i.dosage_per_unit,
          i.features,
          i.url
        FROM
          supplements.journal j
          JOIN supplements.inventory i ON i.id = j.inventory_id
        WHERE
          j.inventory_id = $1
        ORDER BY
          j.started_at
        """,
        inventory_id,
    )
    entries = [_build_journal_entry(row) for row in rows]
    return json.dumps([e.model_dump(mode="json") for e in entries])
