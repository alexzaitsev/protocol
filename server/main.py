# Copyright 2026 Alex Zaitsev
# SPDX-License-Identifier: AGPL-3.0-only

import os

import uvicorn
from starlette.applications import Starlette
from starlette.routing import Mount

import features.supplements  # noqa: F401 — register MCP
import features.user  # noqa: F401 — register MCP
from app import auth_provider, mcp


def create_app() -> Starlette:
    """Expose FastMCP's OAuth discovery routes at the domain root."""
    mcp_app = mcp.http_app(path="/mcp")
    return Starlette(
        routes=[
            *auth_provider.get_well_known_routes(mcp_path="/mcp"),
            Mount("/", app=mcp_app),
        ],
        lifespan=mcp_app.lifespan,
    )


def main():
    uvicorn.run(
        create_app(),
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "8000")),
    )


if __name__ == "__main__":
    main()
