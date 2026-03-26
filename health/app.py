import os
from contextlib import asynccontextmanager

from data.db import close_pool, init_pool
from fastmcp import FastMCP
from fastmcp.server.auth.providers.google import GoogleProvider


@asynccontextmanager
async def lifespan(server):
    await init_pool()
    try:
        yield
    finally:
        await close_pool()


auth_provider = GoogleProvider(
    client_id=os.environ["GOOGLE_CLIENT_ID"],
    client_secret=os.environ["GOOGLE_CLIENT_SECRET"],
    base_url=os.environ["MCP_SERVER_URL"] or "http://localhost:8000",
    required_scopes=[
        "openid",
        "https://www.googleapis.com/auth/userinfo.email",
    ],
)

mcp = FastMCP(
    name="Family Health",
    version="1.0.0",
    website_url="https://github.com/alexzaitsev/family-health",
    auth=auth_provider,
    lifespan=lifespan,
    instructions="Family health tracking server. Authenticated per-user — all data is scoped to the signed-in user via OAuth.",
)
