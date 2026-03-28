# Copyright 2026 Alex Zaitsev
# SPDX-License-Identifier: AGPL-3.0-only

import features.user  # noqa: F401 — register MCP
from app import mcp


def main():
    mcp.run(
        transport="streamable-http",
        host="0.0.0.0",
    )


if __name__ == "__main__":
    main()
