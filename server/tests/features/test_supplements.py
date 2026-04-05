# Copyright 2026 Alex Zaitsev
# SPDX-License-Identifier: AGPL-3.0-only

from datetime import date

import asyncpg
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


_LOOKUP_QUERY = """
SELECT
  *
FROM
  supplements.inventory
WHERE
  name ILIKE '%' || $1 || '%'
  OR brand ILIKE '%' || $1 || '%'
ORDER BY
  name
"""

_ADD_INVENTORY_QUERY = """
INSERT INTO supplements.inventory (name, brand, category, form,
  dosage_per_unit, features, url)
VALUES ($1, $2, $3, $4, $5, $6, $7)
RETURNING *
"""


class TestLookupInventory:
    async def test_match_by_name(self, db_conn):
        await _insert_inventory(db_conn, name="Vitamin D3", brand="Jamieson")
        await _insert_inventory(db_conn, name="Omega-3", brand="Nordic Naturals")

        rows = await db_conn.fetch(_LOOKUP_QUERY, "vitamin")
        assert len(rows) == 1
        assert rows[0]["name"] == "Vitamin D3"

    async def test_match_by_brand(self, db_conn):
        await _insert_inventory(db_conn, name="Vitamin D3", brand="Jamieson")
        await _insert_inventory(db_conn, name="Omega-3", brand="Nordic Naturals")

        rows = await db_conn.fetch(_LOOKUP_QUERY, "Nordic")
        assert len(rows) == 1
        assert rows[0]["name"] == "Omega-3"

    async def test_case_insensitive(self, db_conn):
        await _insert_inventory(db_conn, name="Vitamin D3", brand="Jamieson")

        rows = await db_conn.fetch(_LOOKUP_QUERY, "VITAMIN")
        assert len(rows) == 1

    async def test_partial_match(self, db_conn):
        await _insert_inventory(db_conn, name="Vitamin D3")
        await _insert_inventory(db_conn, name="Vitamin C")

        rows = await db_conn.fetch(_LOOKUP_QUERY, "Vitamin")
        assert len(rows) == 2

    async def test_no_matches_returns_empty(self, db_conn):
        await _insert_inventory(db_conn, name="Vitamin D3")

        rows = await db_conn.fetch(_LOOKUP_QUERY, "nonexistent_xyz_abc")
        assert rows == []


class TestAddInventory:
    async def test_creates_item_returns_id(self, db_conn):
        row = await db_conn.fetchrow(
            _ADD_INVENTORY_QUERY,
            "Vitamin D3",
            "Jamieson",
            "vitamin",
            "softgel",
            "1000 IU",
            [],
            None,
        )
        assert row is not None
        assert row["id"] is not None
        assert row["name"] == "Vitamin D3"
        assert row["brand"] == "Jamieson"
        assert row["features"] == []
        assert row["url"] is None

    async def test_creates_item_with_features_and_url(self, db_conn):
        row = await db_conn.fetchrow(
            _ADD_INVENTORY_QUERY,
            "Magnesium Glycinate",
            "Pure Encapsulations",
            "mineral",
            "capsule",
            "120 mg",
            ["chelated", "gentle on stomach"],
            "https://example.com/mag",
        )
        assert row is not None
        assert row["features"] == ["chelated", "gentle on stomach"]
        assert row["url"] == "https://example.com/mag"

    async def test_duplicate_name_brand_raises_unique_violation(self, db_conn):
        await db_conn.fetchrow(
            _ADD_INVENTORY_QUERY,
            "Vitamin D3",
            "Jamieson",
            "vitamin",
            "softgel",
            "1000 IU",
            [],
            None,
        )
        with pytest.raises(asyncpg.UniqueViolationError):
            await db_conn.fetchrow(
                _ADD_INVENTORY_QUERY,
                "Vitamin D3",
                "Jamieson",
                "vitamin",
                "tablet",
                "2000 IU",
                [],
                None,
            )

    async def test_same_name_different_brand_allowed(self, db_conn):
        await db_conn.fetchrow(
            _ADD_INVENTORY_QUERY,
            "Vitamin D3",
            "Jamieson",
            "vitamin",
            "softgel",
            "1000 IU",
            [],
            None,
        )
        row = await db_conn.fetchrow(
            _ADD_INVENTORY_QUERY,
            "Vitamin D3",
            "Now Foods",
            "vitamin",
            "softgel",
            "2000 IU",
            [],
            None,
        )
        assert row is not None
        assert row["brand"] == "Now Foods"


class TestUpdateInventory:
    async def test_updates_single_field(self, db_conn):
        inv_id = await _insert_inventory(db_conn, name="Vitamin D3")

        row = await db_conn.fetchrow(
            "UPDATE supplements.inventory SET url = $1 WHERE id = $2 RETURNING *",
            "https://example.com",
            inv_id,
        )
        assert row["url"] == "https://example.com"
        assert row["name"] == "Vitamin D3"

    async def test_updates_multiple_fields(self, db_conn):
        inv_id = await _insert_inventory(
            db_conn, name="Vitamin D3", form="softgel", dosage_per_unit="1000 IU"
        )

        row = await db_conn.fetchrow(
            "UPDATE supplements.inventory"
            " SET form = $1, dosage_per_unit = $2"
            " WHERE id = $3 RETURNING *",
            "capsule",
            "2000 IU",
            inv_id,
        )
        assert row["form"] == "capsule"
        assert row["dosage_per_unit"] == "2000 IU"
        assert row["name"] == "Vitamin D3"

    async def test_nonexistent_id_returns_none(self, db_conn):
        row = await db_conn.fetchrow(
            "UPDATE supplements.inventory SET url = $1 WHERE id = $2 RETURNING *",
            "https://example.com",
            999999,
        )
        assert row is None

    async def test_duplicate_name_brand_raises_unique_violation(self, db_conn):
        await _insert_inventory(db_conn, name="Vitamin D3", brand="Jamieson")
        inv_id = await _insert_inventory(db_conn, name="Vitamin C", brand="Jamieson")

        with pytest.raises(asyncpg.UniqueViolationError):
            await db_conn.fetchrow(
                "UPDATE supplements.inventory"
                " SET name = $1 WHERE id = $2 RETURNING *",
                "Vitamin D3",
                inv_id,
            )

    async def test_journal_guard_no_entry_blocks_update(self, rls_conn):
        inv_id = await _insert_inventory(rls_conn, name="Vitamin D3")

        row = await rls_conn.fetchrow(
            "SELECT 1 FROM supplements.journal WHERE inventory_id = $1 LIMIT 1",
            inv_id,
        )
        assert row is None

    async def test_journal_guard_with_entry_allows_update(self, rls_conn):
        inv_id = await _insert_inventory(rls_conn, name="Vitamin D3")
        await _insert_journal(rls_conn, inv_id, time_blocks=["morning"])

        row = await rls_conn.fetchrow(
            "SELECT 1 FROM supplements.journal WHERE inventory_id = $1 LIMIT 1",
            inv_id,
        )
        assert row is not None

    async def test_journal_guard_historical_entry_allows_update(self, rls_conn):
        inv_id = await _insert_inventory(rls_conn, name="Vitamin D3")
        await _insert_journal(
            rls_conn,
            inv_id,
            time_blocks=["morning"],
            ended_at=date(2026, 3, 1),
            end_reason="no longer needed",
        )

        row = await rls_conn.fetchrow(
            "SELECT 1 FROM supplements.journal WHERE inventory_id = $1 LIMIT 1",
            inv_id,
        )
        assert row is not None


_ADD_CONTEXT_QUERY = (
    "INSERT INTO supplements.context (user_id, inventory_id, purpose)"
    " VALUES (current_setting('app.current_user_id', true), $1, $2)"
    " RETURNING *"
)

_UPDATE_CONTEXT_QUERY = (
    "UPDATE supplements.context SET purpose = $1 WHERE inventory_id = $2 RETURNING *"
)


class TestAddContext:
    async def test_creates_context_returns_row(self, rls_conn):
        inv_id = await _insert_inventory(rls_conn, name="Vitamin D3")

        row = await rls_conn.fetchrow(_ADD_CONTEXT_QUERY, inv_id, ["bone health"])
        assert row is not None
        assert row["inventory_id"] == inv_id
        assert row["purpose"] == ["bone health"]
        assert row["id"] is not None

    async def test_multiple_purposes(self, rls_conn):
        inv_id = await _insert_inventory(rls_conn, name="Vitamin D3")

        row = await rls_conn.fetchrow(
            _ADD_CONTEXT_QUERY, inv_id, ["bone health", "immune support", "mood"]
        )
        assert row["purpose"] == ["bone health", "immune support", "mood"]

    async def test_duplicate_user_inventory_raises_unique_violation(self, rls_conn):
        inv_id = await _insert_inventory(rls_conn, name="Vitamin D3")
        await rls_conn.fetchrow(_ADD_CONTEXT_QUERY, inv_id, ["bone health"])

        with pytest.raises(asyncpg.UniqueViolationError):
            await rls_conn.fetchrow(_ADD_CONTEXT_QUERY, inv_id, ["immune support"])

    async def test_same_inventory_different_users_allowed(self, db_conn):
        # db_conn is postgres superuser here — rls_conn not requested
        inv_id = await _insert_inventory(db_conn, name="Vitamin D3")

        user1, user2 = "ctx-user-1", "ctx-user-2"
        await db_conn.execute(
            "INSERT INTO person.users (id, google_email, display_name, sex, date_of_birth)"
            " VALUES ($1, $2, $3, $4, $5)",
            user1, "ctx1@example.com", "User", "m", date(2000, 1, 1),
        )
        await db_conn.execute(
            "INSERT INTO person.users (id, google_email, display_name, sex, date_of_birth)"
            " VALUES ($1, $2, $3, $4, $5)",
            user2, "ctx2@example.com", "User", "m", date(2001, 1, 1),
        )

        await db_conn.execute("SET LOCAL ROLE app_user")
        await db_conn.execute(
            "SELECT set_config('app.current_user_id', $1, true)", user1
        )
        row1 = await db_conn.fetchrow(_ADD_CONTEXT_QUERY, inv_id, ["bone health"])
        assert row1 is not None

        await db_conn.execute(
            "SELECT set_config('app.current_user_id', $1, true)", user2
        )
        row2 = await db_conn.fetchrow(_ADD_CONTEXT_QUERY, inv_id, ["immune support"])
        assert row2 is not None
        assert row2["purpose"] == ["immune support"]


class TestUpdateSupplementContext:
    async def test_updates_purpose(self, rls_conn):
        inv_id = await _insert_inventory(rls_conn, name="Vitamin D3")
        await _insert_context(rls_conn, inv_id, ["bone health"])

        row = await rls_conn.fetchrow(
            _UPDATE_CONTEXT_QUERY, ["bone health", "immune support"], inv_id
        )
        assert row is not None
        assert row["purpose"] == ["bone health", "immune support"]

    async def test_replaces_full_purpose_list(self, rls_conn):
        inv_id = await _insert_inventory(rls_conn, name="Vitamin D3")
        await _insert_context(rls_conn, inv_id, ["bone health", "mood"])

        row = await rls_conn.fetchrow(_UPDATE_CONTEXT_QUERY, ["sleep"], inv_id)
        assert row["purpose"] == ["sleep"]

    async def test_no_context_returns_none(self, rls_conn):
        inv_id = await _insert_inventory(rls_conn, name="Vitamin D3")

        row = await rls_conn.fetchrow(_UPDATE_CONTEXT_QUERY, ["bone health"], inv_id)
        assert row is None

    async def test_rls_cannot_update_other_users_context(self, db_conn):
        # db_conn is postgres superuser here — rls_conn not requested
        inv_id = await _insert_inventory(db_conn, name="Vitamin D3")

        user1, user2 = "ctx-rls-1", "ctx-rls-2"
        await db_conn.execute(
            "INSERT INTO person.users (id, google_email, display_name, sex, date_of_birth)"
            " VALUES ($1, $2, $3, $4, $5)",
            user1, "rls1@example.com", "User", "m", date(2000, 1, 1),
        )
        await db_conn.execute(
            "INSERT INTO person.users (id, google_email, display_name, sex, date_of_birth)"
            " VALUES ($1, $2, $3, $4, $5)",
            user2, "rls2@example.com", "User", "m", date(2001, 1, 1),
        )

        # Insert context for user2 as superuser
        await db_conn.execute(
            "INSERT INTO supplements.context (user_id, inventory_id, purpose)"
            " VALUES ($1, $2, $3)",
            user2, inv_id, ["bone health"],
        )

        # Switch to app_user as user1 — UPDATE should not touch user2's row
        await db_conn.execute("SET LOCAL ROLE app_user")
        await db_conn.execute(
            "SELECT set_config('app.current_user_id', $1, true)", user1
        )
        row = await db_conn.fetchrow(_UPDATE_CONTEXT_QUERY, ["mood"], inv_id)
        assert row is None
