import json
import logging
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import asyncpg
from fastmcp.server.dependencies import get_access_token

logger = logging.getLogger(__name__)

_pool: asyncpg.Pool | None = None


def _get_user_email() -> str:
    """Return the current user ID from the OAuth-authenticated request context."""
    token = get_access_token()
    if token is not None:
        email = token.claims.get("email")
        if email is not None:
            return email
    raise RuntimeError("No authenticated user in HTTP request")


async def _get_user_id() -> str:
    email = _get_user_email()
    row = await fetchrow("SELECT id FROM person.users WHERE google_email = $1", email)
    if row is None:
        raise RuntimeError("No user found")
    return row["id"]


async def _init_connection(conn: asyncpg.Connection) -> None:
    await conn.set_type_codec(
        "jsonb",
        encoder=json.dumps,
        decoder=json.loads,
        schema="pg_catalog",
    )


async def init_pool() -> None:
    global _pool
    if _pool is not None:
        return

    dsn = os.environ["DATABASE_URL"]
    try:
        _pool = await asyncpg.create_pool(
            dsn,
            min_size=1,
            max_size=3,
            init=_init_connection,
            statement_cache_size=0,
        )
    except Exception as exc:
        logger.error(
            "Failed to create database pool: %s: %s. Will retry on next request.",
            type(exc).__name__,
            exc,
        )


async def close_pool() -> None:
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


async def get_pool() -> asyncpg.Pool:
    if _pool is None:
        await init_pool()
    assert _pool is not None
    return _pool


async def execute(query: str, *args: object) -> None:
    """Execute a query (INSERT, UPDATE, DELETE) without returning rows."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(query, *args)


async def fetchrow(query: str, *args: object) -> asyncpg.Record | None:
    """Execute a query and return a single row, or None."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetchrow(query, *args)


@asynccontextmanager
async def _rls_connection() -> AsyncIterator[asyncpg.Connection]:
    pool = await get_pool()
    user_id = await _get_user_id()
    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute("SET LOCAL ROLE app_user")
            await conn.execute(
                "SELECT set_config('app.current_user_id', $1, true)", user_id
            )
            yield conn


async def execute_rls(query: str, *args: object) -> None:
    """Execute a query (INSERT, UPDATE, DELETE) within an RLS-scoped transaction."""
    async with _rls_connection() as conn:
        await conn.execute(query, *args)


async def fetchrow_rls(query: str, *args: object) -> asyncpg.Record | None:
    """Execute a query within an RLS-scoped transaction and return one row."""
    async with _rls_connection() as conn:
        return await conn.fetchrow(query, *args)


async def fetch_rls(query: str, *args: object) -> list[asyncpg.Record]:
    """Execute a query within an RLS-scoped transaction and return all rows."""
    async with _rls_connection() as conn:
        return await conn.fetch(query, *args)
