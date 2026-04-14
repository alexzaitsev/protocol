---
title: Development
description: Run the Protocol MCP server locally.
---

## Requirements

- [Python 3.14+](https://www.python.org/) with [uv](https://docs.astral.sh/uv/)
- [Docker](https://www.docker.com/) - required for integration tests (testcontainers)
- [Supabase CLI](https://supabase.com/docs/guides/cli/getting-started) - `brew install supabase/tap/supabase`
- Google Cloud OAuth client configured with localhost redirect URIs (see [Google Cloud](/protocol/guides/prerequisites/google-cloud/) prerequisites)

## Setup

1. Clone your fork and install dependencies:

```bash
git clone https://github.com/<your-username>/protocol.git
cd protocol/server
uv sync
```

2. Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

:::note[SSL certificate]
The `PGSSLROOTCERT` variable points asyncpg to the Supabase CA certificate for `sslmode=verify-full`. The default value `data/prod-ca-2021.crt` is relative to `server/` (the working directory). In production (Docker), the cert is copied to the default location (`~/.postgresql/root.crt`) instead.
:::

3. Link and push database migrations (if not done already):

```bash
supabase login
supabase link --project-ref <project-ref>
supabase db push
```

## Run

**VSCode:** Open the project, press **F5** (or **Run → Start Debugging**). The launch config (`.vscode/launch.json`) loads `.env` automatically and starts the server with the debugger attached.

**Terminal:**

```bash
cd server
uv run main.py
```

The server starts at `http://localhost:8000`.

## Test authorization

1. Run [MCP Inspector](https://github.com/modelcontextprotocol/inspector) locally:

```bash
npx @modelcontextprotocol/inspector
```

2. Set the connection URL to `http://localhost:8000/mcp`
3. Authenticate using "OAuth Authentication" - "Quick OAuth Flow"
4. Click **Connect**
5. Use Inspector to query Resources, Tools, Prompts, etc.
