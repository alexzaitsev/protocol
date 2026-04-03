# Copyright 2026 Alex Zaitsev
# SPDX-License-Identifier: AGPL-3.0-only

from datetime import date

import pytest

pytestmark = pytest.mark.integration

TEST_USER_ID = "test-user"

HISTORY_QUERY = """
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
"""

PROTOCOL_QUERY = """
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


async def _insert_inventory(
    conn,
    *,
    name,
    brand="TestBrand",
    category="vitamin",
    form="capsule",
    dosage_per_unit="1000 mg",
):
    row = await conn.fetchrow(
        "INSERT INTO supplements.inventory (name, brand, category, form, dosage_per_unit)"
        " VALUES ($1, $2, $3, $4, $5) RETURNING id",
        name,
        brand,
        category,
        form,
        dosage_per_unit,
    )
    return row["id"]


async def _insert_journal(
    conn,
    inventory_id,
    *,
    time_blocks,
    dosage="1 cap",
    frequency="daily",
    started_at=None,
    ended_at=None,
    end_reason=None,
    replaces_id=None,
    replacement_reason=None,
):
    started = started_at or date(2026, 1, 1)
    return await conn.fetchrow(
        "INSERT INTO supplements.journal"
        " (user_id, inventory_id, time_blocks, dosage, frequency, started_at,"
        " ended_at, end_reason, replaces_id, replacement_reason)"
        " VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10) RETURNING *",
        TEST_USER_ID,
        inventory_id,
        time_blocks,
        dosage,
        frequency,
        started,
        ended_at,
        end_reason,
        replaces_id,
        replacement_reason,
    )


async def _insert_context(conn, inventory_id, purpose):
    await conn.execute(
        "INSERT INTO supplements.context (user_id, inventory_id, purpose)"
        " VALUES ($1, $2, $3)",
        TEST_USER_ID,
        inventory_id,
        purpose,
    )


class TestGetSupplementProtocol:
    async def test_empty_protocol(self, rls_conn):
        rows = await rls_conn.fetch(PROTOCOL_QUERY)
        assert rows == []

    async def test_single_active_supplement(self, rls_conn):
        inv_id = await _insert_inventory(rls_conn, name="Vitamin D3")
        await _insert_journal(rls_conn, inv_id, time_blocks=["morning"])
        await _insert_context(rls_conn, inv_id, ["bone health", "immune support"])

        rows = await rls_conn.fetch(PROTOCOL_QUERY)
        assert len(rows) == 1
        r = rows[0]
        assert r["inv_name"] == "Vitamin D3"
        assert r["inventory_id"] == inv_id
        assert r["time_blocks"] == ["morning"]
        assert r["purpose"] == ["bone health", "immune support"]
        assert r["ended_at"] is None

    async def test_ordering_by_time_block(self, rls_conn):
        inv_evening = await _insert_inventory(rls_conn, name="Magnesium")
        inv_morning = await _insert_inventory(rls_conn, name="Vitamin D3")
        inv_any = await _insert_inventory(rls_conn, name="Omega-3")

        await _insert_journal(rls_conn, inv_evening, time_blocks=["evening"])
        await _insert_journal(rls_conn, inv_morning, time_blocks=["morning"])
        await _insert_journal(rls_conn, inv_any, time_blocks=["any"])

        rows = await rls_conn.fetch(PROTOCOL_QUERY)
        names = [r["inv_name"] for r in rows]
        assert names == ["Omega-3", "Vitamin D3", "Magnesium"]

    async def test_ended_supplement_excluded(self, rls_conn):
        inv_active = await _insert_inventory(rls_conn, name="Vitamin D3")
        inv_ended = await _insert_inventory(rls_conn, name="Zinc")

        await _insert_journal(rls_conn, inv_active, time_blocks=["morning"])
        await _insert_journal(
            rls_conn,
            inv_ended,
            time_blocks=["morning"],
            ended_at=date(2026, 3, 1),
            end_reason="no longer needed",
        )

        rows = await rls_conn.fetch(PROTOCOL_QUERY)
        assert len(rows) == 1
        assert rows[0]["inv_name"] == "Vitamin D3"

    async def test_context_optional(self, rls_conn):
        inv_id = await _insert_inventory(rls_conn, name="Vitamin C")
        await _insert_journal(rls_conn, inv_id, time_blocks=["lunch"])

        rows = await rls_conn.fetch(PROTOCOL_QUERY)
        assert len(rows) == 1
        assert rows[0]["purpose"] is None


class TestGetSupplementHistory:
    async def test_empty_history(self, rls_conn):
        inv_id = await _insert_inventory(rls_conn, name="Vitamin D3")
        rows = await rls_conn.fetch(HISTORY_QUERY, inv_id)
        assert rows == []

    async def test_single_active_entry(self, rls_conn):
        inv_id = await _insert_inventory(rls_conn, name="Vitamin D3")
        await _insert_journal(rls_conn, inv_id, time_blocks=["morning"])

        rows = await rls_conn.fetch(HISTORY_QUERY, inv_id)
        assert len(rows) == 1
        assert rows[0]["inv_name"] == "Vitamin D3"
        assert rows[0]["ended_at"] is None
        assert rows[0]["replaces_id"] is None

    async def test_replacement_chain_chronological_order(self, rls_conn):
        inv_id = await _insert_inventory(rls_conn, name="Magnesium")

        row_a = await _insert_journal(
            rls_conn,
            inv_id,
            time_blocks=["evening"],
            dosage="200 mg",
            started_at=date(2026, 1, 1),
            ended_at=date(2026, 2, 1),
            end_reason="dosage increase",
        )
        row_b = await _insert_journal(
            rls_conn,
            inv_id,
            time_blocks=["evening"],
            dosage="400 mg",
            started_at=date(2026, 2, 1),
            ended_at=date(2026, 3, 1),
            end_reason="timing change",
            replaces_id=row_a["id"],
            replacement_reason="dosage increase",
        )
        await _insert_journal(
            rls_conn,
            inv_id,
            time_blocks=["morning"],
            dosage="400 mg",
            started_at=date(2026, 3, 1),
            replaces_id=row_b["id"],
            replacement_reason="timing change",
        )

        rows = await rls_conn.fetch(HISTORY_QUERY, inv_id)
        assert len(rows) == 3
        assert rows[0]["dosage"] == "200 mg"
        assert rows[0]["replaces_id"] is None
        assert rows[1]["dosage"] == "400 mg"
        assert rows[1]["replaces_id"] == row_a["id"]
        assert rows[1]["replacement_reason"] == "dosage increase"
        assert rows[2]["time_blocks"] == ["morning"]
        assert rows[2]["replaces_id"] == row_b["id"]
        assert rows[2]["ended_at"] is None

    async def test_only_returns_requested_supplement(self, rls_conn):
        inv_a = await _insert_inventory(rls_conn, name="Vitamin D3")
        inv_b = await _insert_inventory(rls_conn, name="Omega-3")
        await _insert_journal(rls_conn, inv_a, time_blocks=["morning"])
        await _insert_journal(rls_conn, inv_b, time_blocks=["lunch"])

        rows = await rls_conn.fetch(HISTORY_QUERY, inv_a)
        assert len(rows) == 1
        assert rows[0]["inventory_id"] == inv_a
