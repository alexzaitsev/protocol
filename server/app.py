import os
from contextlib import asynccontextmanager

import asyncpg
from data.db import close_pool, init_pool
from fastmcp import FastMCP
from fastmcp.server.auth.providers.google import GoogleProvider
from key_value.aio.stores.postgresql import PostgreSQLStore
from key_value.aio.wrappers.encryption import FernetEncryptionWrapper


class _SupabaseKVStore(PostgreSQLStore):
    """PostgreSQLStore with statement_cache_size=0 for Supabase transaction pooler."""

    async def _create_pool(self) -> asyncpg.Pool:
        return await asyncpg.create_pool(
            self._url, statement_cache_size=0, min_size=1, max_size=2
        )


@asynccontextmanager
async def lifespan(server):
    await init_pool()
    try:
        yield
    finally:
        await close_pool()


oauth_store = FernetEncryptionWrapper(
    key_value=_SupabaseKVStore(
        url=os.environ["DATABASE_URL"], table_name="google_oauth"
    ),
    source_material=os.environ["GOOGLE_CLIENT_SECRET"],
    salt="protocol-oauth",
)

auth_provider = GoogleProvider(
    client_id=os.environ["GOOGLE_CLIENT_ID"],
    client_secret=os.environ["GOOGLE_CLIENT_SECRET"],
    base_url=os.environ["MCP_SERVER_URL"] or "http://localhost:8000",
    required_scopes=[
        "openid",
        "https://www.googleapis.com/auth/userinfo.email",
    ],
    client_storage=oauth_store,
)

mcp = FastMCP(
    name="Protocol",
    version="1.0.0",
    website_url="https://github.com/alexzaitsev/protocol",
    auth=auth_provider,
    lifespan=lifespan,
    instructions="Protocol server. Authenticated per-user — all data is scoped to the signed-in user via OAuth.",
)
