# Copyright 2026 Alex Zaitsev
# SPDX-License-Identifier: AGPL-3.0-only

from datetime import date
from pathlib import Path

import asyncpg
import pytest
from data.db import _init_connection
from testcontainers.postgres import PostgresContainer

MIGRATIONS_DIR = Path(__file__).resolve().parents[2] / "supabase" / "migrations"

TEST_USER_ID = "test-user"
TEST_USER_EMAIL = "test@example.com"


@pytest.fixture(scope="session")
def pg_container():
    with PostgresContainer("postgres:17", username="postgres", driver=None) as pg:
        yield pg


@pytest.fixture(scope="session")
async def pg_pool(pg_container):
    url = pg_container.get_connection_url().replace("+psycopg2", "")
    pool = await asyncpg.create_pool(url, min_size=1, max_size=3, init=_init_connection)
    async with pool.acquire() as conn:
        for mf in sorted(MIGRATIONS_DIR.glob("*.sql")):
            await conn.execute(mf.read_text())
    yield pool
    await pool.close()


@pytest.fixture
async def db_conn(pg_pool):
    async with pg_pool.acquire() as conn:
        tx = conn.transaction()
        await tx.start()
        yield conn
        await tx.rollback()


@pytest.fixture
async def rls_conn(db_conn):
    await db_conn.execute(
        "INSERT INTO person.users (id, google_email, display_name, sex, date_of_birth)"
        " VALUES ($1, $2, $3, $4, $5) ON CONFLICT DO NOTHING",
        TEST_USER_ID,
        TEST_USER_EMAIL,
        "Test User",
        "m",
        date(2000, 1, 1),
    )
    await db_conn.execute("SET LOCAL ROLE app_user")
    await db_conn.execute(
        "SELECT set_config('app.current_user_id', $1, true)", TEST_USER_ID
    )
    yield db_conn
