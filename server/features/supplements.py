# Copyright 2026 Alex Zaitsev
# SPDX-License-Identifier: AGPL-3.0-only

import json
from datetime import date
from enum import StrEnum

import asyncpg
from app import mcp
from data.db import fetch, fetch_rls, fetchrow_rls
from pydantic import BaseModel, Field
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


@mcp.tool(
    name="lookup_inventory",
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
    name="get_supplement_protocol",
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


@mcp.tool(
    name="get_supplement",
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
