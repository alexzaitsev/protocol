---
title: Overview
description: How Protocol's pieces fit together.
---

Protocol is a Python MCP server built with [FastMCP](https://github.com/jlowin/fastmcp). It connects to Supabase PostgreSQL via asyncpg and uses streamable HTTP transport with OAuth 2.1 (Google) for authentication. Row-Level Security (RLS) enforces per-user data isolation at the database level.

The server exposes MCP tools that AI assistants call on your behalf - querying your supplement protocol, recording blood tests, running duration reviews, generating protocol documents. The LLM handles natural language understanding, PDF parsing, and analytical reasoning; the server handles structured data, transactions, and access control.

**Architecture:** Claude/any MCP client → MCP server (Fly.io) → Supabase PostgreSQL

## Key design decisions

- SCD Type 2 for supplement history (point-in-time protocol reconstruction)
- Atomic transactions for all mutations (no orphaned or inconsistent state)
- AI-first interface (no GUI - the LLM is the UX layer)
- Self-hosted, open-source, no vendor lock-in
