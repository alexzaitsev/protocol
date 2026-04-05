# Copyright 2026 Alex Zaitsev
# SPDX-License-Identifier: AGPL-3.0-only

import base64
import json
import os
from contextlib import asynccontextmanager

import asyncpg
from data.db import close_pool, fetchrow, init_pool
from fastmcp import FastMCP
from fastmcp.server.auth.providers.google import GoogleProvider
from key_value.aio.stores.postgresql import PostgreSQLStore
from key_value.aio.wrappers.encryption import FernetEncryptionWrapper
from mcp.server.auth.provider import AuthorizationCode, TokenError
from mcp.shared.auth import OAuthClientInformationFull, OAuthToken


class _SupabaseKVStore(PostgreSQLStore):
    """PostgreSQLStore with statement_cache_size=0 for Supabase transaction pooler."""

    async def _create_pool(self) -> asyncpg.Pool:
        return await asyncpg.create_pool(
            self._url, statement_cache_size=0, min_size=1, max_size=2
        )


class _AllowlistGoogleProvider(GoogleProvider):
    """GoogleProvider that rejects token exchange for emails not in person.users."""

    async def exchange_authorization_code(
        self,
        client: OAuthClientInformationFull,
        authorization_code: AuthorizationCode,
    ) -> OAuthToken:
        code_model = await self._code_store.get(key=authorization_code.code)
        if code_model is None:
            raise TokenError("invalid_grant", "Authorization code not found")

        try:
            id_token = code_model.idp_tokens["id_token"]
            payload_b64 = id_token.split(".")[1]
            payload_b64 += "=" * (4 - len(payload_b64) % 4)
            email = json.loads(base64.urlsafe_b64decode(payload_b64)).get("email")
        except Exception:
            raise TokenError("invalid_grant", "User not authorized")

        if not email:
            raise TokenError("invalid_grant", "User not authorized")

        row = await fetchrow(
            "SELECT id FROM person.users WHERE google_email = $1", email
        )
        if row is None:
            raise TokenError("invalid_grant", "User not authorized")

        return await super().exchange_authorization_code(client, authorization_code)


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

auth_provider = _AllowlistGoogleProvider(
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
