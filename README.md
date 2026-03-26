# Family Health

An MCP server for tracking family health data — supplements, blood tests, health profiles, and knowledge. Backed by Supabase PostgreSQL.

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
  - [Supabase](#supabase)
  - [Google Cloud](#google-cloud)
- [Fork and configure](#fork-and-configure)
- [Deployment](#deployment)
- [Development](#development)

# Overview

The MCP server (Python / FastMCP) connects to Supabase PostgreSQL via asyncpg. It uses streamable HTTP transport with OAuth 2.1 (Google) for authentication. Row-Level Security (RLS) enforces per-user data isolation at the database level.

# Prerequisites

Sign up for these services:

- [Supabase](https://supabase.com/) — PostgreSQL database
- [Google Cloud](https://console.cloud.google.com/) — OAuth 2.0 (Google sign-in)

<details>
<summary><h2>Supabase</h2></summary>

Supabase provides the PostgreSQL database. You'll set up a project, link it locally, and construct a connection URL that the MCP server uses at runtime.

### Create a project

1. Go to [supabase.com/dashboard](https://supabase.com/dashboard) and create an account
2. Click **New Project**, choose an organization, set a project name, database password, and region
3. Note the **Project Reference ID** from the project URL: `https://supabase.com/dashboard/project/<project-ref>`

### Construct the connection URL

The MCP server connects via asyncpg using a `DATABASE_URL` environment variable. Build it from your Supabase dashboard:

1. Go to **Connect** → **Connection String** → **Transaction pooler** (port `6543`)
2. The URL follows this format:

```
postgresql://postgres.<project-ref>:<password>@<pooler-host>:6543/postgres?sslmode=verify-full
```

- **`<pooler-host>`** — copy the host from the transaction pooler connection string
- **`<password>`** — your database password, URL-encoded (special characters like `@`, `!`, `#`, `%` must be escaped, e.g. `p@ss!` → `p%40ss%21`)

Save this URL.

### Connection details

- **Transaction pooler (port `6543`)** is required. It assigns a dedicated server connection per transaction, which is what makes `SET LOCAL ROLE` and `set_config(..., true)` work correctly for RLS
- Connect as **`postgres`** — the only role Supavisor recognizes. The code downgrades to `app_user` via `SET LOCAL ROLE` inside each RLS transaction
- **`statement_cache_size=0`** is required because the transaction pooler does not support `PREPARE` statements
- **`sslmode=verify-full`** is required for remote connections
- Do **not** use session-level settings (`SET` without `LOCAL`) — they won't persist across requests in the transaction pooler

</details>

<details>
<summary><h2>Google Cloud</h2></summary>

Google Cloud provides OAuth 2.0 for user authentication. Since this is a family-scoped project, the app stays in **Testing** mode — only listed test users can authenticate, no Google verification needed.

### Create a project

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Click the project dropdown → **New Project**
3. Enter a name (e.g. "Family Health MCP") → **Create**

### Configure OAuth consent

Google has renamed "OAuth consent screen" to **Google Auth Platform**. Navigate to **Menu → Google Auth Platform** (or the legacy path *APIs & Services → OAuth consent screen*, which redirects).

1. Click **Get Started**
2. **App Information**: enter app name, select support email → **Next**
3. **Audience**: choose **External** → **Next**
4. **Contact Information**: enter notification email → **Next**
5. **Agree** to terms → **Create**

After creation:

6. Go to **Audience** → keep **Testing** status (limits to 100 test users — more than enough for family)
7. Under **Test users**, click **Add users** → add family member email addresses
8. Go to **Data Access** → **Add or Remove Scopes** → add `openid` and `email` (both non-sensitive) → **Update** → **Save**

### Create OAuth credentials

Navigate to **Google Auth Platform → Clients** (or legacy *APIs & Services → Credentials*).

1. Click **Create Client** (or *Create Credentials → OAuth client ID*)
2. Application type: **Web application**
3. Name: anything (e.g. "Family Health MCP")
4. Under **Authorized JavaScript origins**, add your server's base URL (e.g. `https://your-production-domain.com`)
5. Under **Authorized redirect URIs**, add your server's callback URL: `https://your-production-domain.com/auth/callback`
6. Click **Create**
7. Copy the **Client ID** and **Client Secret** — store them securely
8. Optionally click **Download JSON** to save the credentials file

**Local development (optional):** To run the server locally, add these to the same OAuth client:

- **Authorized JavaScript origins:** `http://localhost:8000`
- **Authorized redirect URIs:** `http://localhost:8000/auth/callback`

Google allows multiple origins and redirect URIs per client, so both local and production can coexist.

</details>

# Fork and configure

1. [Fork this repository](https://github.com/alexzaitsev/family-health/fork) on GitHub
2. In your fork, go to **Settings** → **Secrets and variables** → **Actions** → **New repository secret**
3. Add these secrets:

| Secret | Value | Where to get it |
|--------|-------|-----------------|
| `SUPABASE_ACCESS_TOKEN` | Supabase personal access token | [supabase.com/dashboard/account/tokens](https://supabase.com/dashboard/account/tokens) |
| `SUPABASE_PROJECT_ID` | Project reference ID | From the project URL: `supabase.com/dashboard/project/<project-ref>` |
| `SUPABASE_DB_PASSWORD` | Database password | Set during project creation |

These secrets are used by the deploy workflow (`.github/workflows/deploy.yml`) to automatically push database migrations on every push to `main`. You can trigger workflow manually from Actions. 

# Deployment

## Apply Supabase migrations and deploy MCP server

Trigger manual `deploy` workflow from Actions. 

## Add family members to Supabase

Add each family member via the Supabase SQL Editor:

1. Go to **Supabase Dashboard** → your project → **SQL Editor**
2. Run the following SQL for each user (replace placeholder values):

```sql
INSERT INTO person.users (id, google_email, display_name, sex, date_of_birth)
VALUES ('your_user_id', 'user@gmail.com', 'Display Name', 'm', '2000-01-01');

INSERT INTO person.health_profiles (user_id) VALUES ('your_user_id');
INSERT INTO person.preferences (user_id) VALUES ('your_user_id');
```

- **`id`** — a short text slug used throughout the system (e.g. `jane`)
- **`google_email`** — must match the Google account used to sign in via OAuth
- **`sex`** — `m` or `f`
- `health_profiles` and `preferences` rows are required — defaults are fine to start, update them later

To remove a user, delete their row from `person.users` — all user-specific rows (`health_profiles`, `preferences`) are removed automatically via cascading deletes. Shared tables are left intact.

# Give it a try!

Connect the MCP server to your preferred AI client:

**Claude.ai:**

1. Go to [claude.ai](https://claude.ai) → **Settings** → **Integrations** → **Add More**
2. Enter your server URL: `https://your-production-domain.com/mcp`
3. Click **Connect** → authenticate with your Google account when prompted

**Claude Desktop:**

Add to your Claude Desktop config (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "family-health": {
      "url": "https://your-production-domain.com/mcp"
    }
  }
}
```

Restart Claude Desktop and authenticate when prompted.

**Other MCP clients:**

Any client that supports streamable HTTP transport with OAuth can connect using the server URL: `https://your-production-domain.com/mcp`

# Development

### Requirements

- [Python 3.14+](https://www.python.org/) with [uv](https://docs.astral.sh/uv/)
- [Supabase CLI](https://supabase.com/docs/guides/cli/getting-started) — `brew install supabase/tap/supabase`
- Google Cloud OAuth client configured with localhost redirect URIs (see [Google Cloud](#google-cloud) prerequisites)

### Setup

1. Clone your fork and install dependencies:

```bash
git clone https://github.com/<your-username>/family-health.git
cd family-health/health
uv sync
```

2. Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

> **SSL certificate:** The `PGSSLROOTCERT` variable points asyncpg to the Supabase CA certificate for `sslmode=verify-full`. The default value `data/prod-ca-2021.crt` is relative to `health/` (the working directory). In production (Docker), the cert is copied to the default location (`~/.postgresql/root.crt`) instead.

3. Link and push database migrations (if not done already):

```bash
supabase login
supabase link --project-ref <project-ref>
supabase db push
```

### Run

**VSCode:** Open the project, press **F5** (or **Run → Start Debugging**). The launch config (`.vscode/launch.json`) loads `.env` automatically and starts the server with the debugger attached.

**Terminal:**

```bash
cd health
uv run main.py
```

The server starts at `http://localhost:8000`.

### Test authorization

1. Run [MCP Inspector](https://github.com/modelcontextprotocol/inspector) locally:

```bash
npx @modelcontextprotocol/inspector
```

2. Set the connection URL to `http://localhost:8000/mcp`
3. Authenticate using "OAuth Authentication" - "Quick OAuth Flow"
4. Click **Connect**
5. Use Inspector to query Resources, Tools, Prompts, etc.