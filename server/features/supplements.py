# Copyright 2026 Alex Zaitsev
# SPDX-License-Identifier: AGPL-3.0-only

from app import mcp
from data.db import fetch
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
) -> list[InventoryItem]:
    rows = await fetch(
        "SELECT * FROM supplements.inventory"
        " WHERE name ILIKE '%' || $1 || '%'"
        "    OR brand ILIKE '%' || $1 || '%'"
        " ORDER BY name",
        query,
    )
    return [InventoryItem(**dict(r)) for r in rows]
