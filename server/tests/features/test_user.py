# Copyright 2026 Alex Zaitsev
# SPDX-License-Identifier: AGPL-3.0-only

import pytest

from tests.conftest import TEST_USER_ID

pytestmark = pytest.mark.integration

_CONTEXT_QUERY = """
SELECT
  u.display_name,
  u.sex,
  u.date_of_birth,
  h.conditions,
  h.family_history,
  h.substances,
  h.diet_notes,
  h.activity_notes,
  h.safety_checks,
  h.methodology_notes,
  h.health_priorities,
  p.location,
  p.occupation,
  p.language,
  p.units,
  p.currency,
  p.date_format,
  p.communication
FROM
  person.users u
  INNER JOIN person.health_profiles h ON h.user_id = u.id
  INNER JOIN person.preferences p ON p.user_id = u.id
"""


async def _insert_health_profile(
    conn,
    *,
    conditions=None,
    family_history=None,
    substances=None,
    diet_notes=None,
    activity_notes=None,
    safety_checks=None,
    methodology_notes=None,
    health_priorities=None,
):
    await conn.execute(
        "INSERT INTO person.health_profiles"
        " (user_id, conditions, family_history, substances,"
        "  diet_notes, activity_notes, safety_checks, methodology_notes, health_priorities)"
        " VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)",
        TEST_USER_ID,
        conditions or [],
        family_history or [],
        substances or [],
        diet_notes,
        activity_notes,
        safety_checks or [],
        methodology_notes,
        health_priorities or [],
    )


async def _insert_preferences(
    conn,
    *,
    location=None,
    occupation=None,
    language="en",
    units="metric",
    currency="USD",
    date_format="YYYY-MM-DD",
    communication=None,
):
    await conn.execute(
        "INSERT INTO person.preferences"
        " (user_id, location, occupation, language, units, currency, date_format, communication)"
        " VALUES ($1, $2, $3, $4, $5, $6, $7, $8)",
        TEST_USER_ID,
        location,
        occupation,
        language,
        units,
        currency,
        date_format,
        communication,
    )


class TestGetUserContext:
    async def test_missing_health_profile_returns_none(self, rls_conn):
        row = await rls_conn.fetchrow(_CONTEXT_QUERY)
        assert row is None

    async def test_missing_preferences_returns_none(self, rls_conn):
        await _insert_health_profile(rls_conn)
        row = await rls_conn.fetchrow(_CONTEXT_QUERY)
        assert row is None

    async def test_returns_full_context(self, rls_conn):
        await _insert_health_profile(
            rls_conn,
            conditions=[{"name": "Hypertension", "status": "active", "notes": None}],
            health_priorities=["cardiovascular health"],
        )
        await _insert_preferences(rls_conn, language="fr", currency="CAD")

        row = await rls_conn.fetchrow(_CONTEXT_QUERY)
        assert row is not None
        assert row["display_name"] == "Test User"
        assert row["sex"] == "m"
        assert row["language"] == "fr"
        assert row["currency"] == "CAD"
        assert row["conditions"] == [
            {"name": "Hypertension", "status": "active", "notes": None}
        ]
        assert row["health_priorities"] == ["cardiovascular health"]

    async def test_optional_fields_are_none(self, rls_conn):
        await _insert_health_profile(rls_conn)
        await _insert_preferences(rls_conn)

        row = await rls_conn.fetchrow(_CONTEXT_QUERY)
        assert row["diet_notes"] is None
        assert row["location"] is None
        assert row["communication"] is None

    async def test_defaults(self, rls_conn):
        await _insert_health_profile(rls_conn)
        await _insert_preferences(rls_conn)

        row = await rls_conn.fetchrow(_CONTEXT_QUERY)
        assert row["units"] == "metric"
        assert row["currency"] == "USD"
        assert row["date_format"] == "YYYY-MM-DD"
        assert row["language"] == "en"
