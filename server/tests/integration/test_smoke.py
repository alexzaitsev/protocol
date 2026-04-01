# Copyright 2026 Alex Zaitsev
# SPDX-License-Identifier: AGPL-3.0-only

from datetime import date

import pytest

pytestmark = pytest.mark.integration

EXPECTED_TABLES = {
    ("person", "users"),
    ("person", "health_profiles"),
    ("person", "preferences"),
    ("supplements", "inventory"),
    ("supplements", "journal"),
    ("supplements", "context"),
}


class TestMigrations:
    async def test_tables_exist(self, db_conn):
        rows = await db_conn.fetch(
            "SELECT schemaname, tablename FROM pg_catalog.pg_tables"
            " WHERE schemaname IN ('person', 'supplements')"
        )
        tables = {(r["schemaname"], r["tablename"]) for r in rows}
        assert tables == EXPECTED_TABLES


class TestRLS:
    async def test_read_own_data(self, rls_conn):
        await rls_conn.execute(
            "INSERT INTO person.health_profiles (user_id) VALUES ($1)", "test-user"
        )
        row = await rls_conn.fetchrow("SELECT * FROM person.health_profiles")
        assert row is not None
        assert row["user_id"] == "test-user"

    async def test_cannot_read_other_user(self, db_conn):
        # Seed two users as postgres (superuser)
        await db_conn.execute(
            "INSERT INTO person.users (id, google_email, display_name, sex, date_of_birth)"
            " VALUES ($1, $2, $3, $4, $5), ($6, $7, $8, $9, $10)",
            "user-a",
            "a@example.com",
            "User A",
            "m",
            date(2000, 1, 1),
            "user-b",
            "b@example.com",
            "User B",
            "f",
            date(2000, 1, 1),
        )
        await db_conn.execute(
            "INSERT INTO person.health_profiles (user_id) VALUES ($1), ($2)",
            "user-a",
            "user-b",
        )
        # Switch to app_user as user-a
        await db_conn.execute("SET LOCAL ROLE app_user")
        await db_conn.execute(
            "SELECT set_config('app.current_user_id', $1, true)", "user-a"
        )
        rows = await db_conn.fetch("SELECT user_id FROM person.health_profiles")
        assert [r["user_id"] for r in rows] == ["user-a"]
