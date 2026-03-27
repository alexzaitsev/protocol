# Family Health

An MCP server for tracking family health data — supplements, blood tests, health profiles, and knowledge. Backed by Supabase PostgreSQL.

# Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
  - [Supabase](#supabase)
  - [Google Cloud](#google-cloud)
  - [Fly.io](#flyio)
- [Deployment](#deployment)
- [Development](#development)

# Overview

The MCP server (Python / FastMCP) connects to Supabase PostgreSQL via asyncpg. It uses streamable HTTP transport with OAuth 2.1 (Google) for authentication. Row-Level Security (RLS) enforces per-user data isolation at the database level.

# Prerequisites

Sign up for these services:

- [Supabase](https://supabase.com/) — PostgreSQL database
- [Google Cloud](https://console.cloud.google.com/) — OAuth 2.0 (Google sign-in)
- [Fly.io](https://fly.io/) — MCP server hosting

<details>
<summary><h2>Supabase</h2></summary>

Supabase provides the PostgreSQL database. You'll set up a project, link it locally, and construct a connection URL that the MCP server uses at runtime.

### Create a project

1. Go to [supabase.com/dashboard](https://supabase.com/dashboard) and create an account
2. Click **New Project**, choose an organization, set a project name, database password, and region
3. Note the **Project Reference ID** from the project URL: `https://supabase.com/dashboard/project/<project-ref>`

### Enforce SSL

For extra security it's recommended to enable "Enforce SSL on incoming connections" setting.
It can be found using next link: https://supabase.com/dashboard/project/<project-ref>/database/settings#ssl-configuration

### Construct the connection URL

The MCP server connects via asyncpg using a `DATABASE_URL` environment variable. Build it from your Supabase dashboard:

1. Go to **Connect** → **Connection String** → **Transaction pooler** (port `6543`)
2. The URL follows this format:

```
postgresql://postgres.<project-ref>:<password>@<pooler-host>:6543/postgres?sslmode=verify-full
```

- **`<pooler-host>`** — copy the host from the transaction pooler connection string
- **`<password>`** — your database password, URL-encoded (special characters like `@`, `!`, `#`, `%` must be escaped, e.g. `p@ss!` → `p%40ss%21`)

### Outputs

After completing this step you should have the next values:  

| Key | Value | Where to get it | Purpose | 
|--------|-------|-----------------|--------|
| `SUPABASE_ACCESS_TOKEN` | Supabase personal access token | [supabase.com/dashboard/account/tokens](https://supabase.com/dashboard/account/tokens) | Github secret | 
| `SUPABASE_PROJECT_ID` | Project reference ID | From the project URL: `supabase.com/dashboard/project/<project-ref>` | Github secret |
| `SUPABASE_DB_PASSWORD` | Database password | Set during [project creation](#create-a-project) | Github secret |
| `DATABASE_URL` | Connection URL | See [here](#construct-the-connection-url) | Server secret |

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

### Outputs

After completing this step you should have the next values:  

| Key | Value | Where to get it | Purpose | 
|--------|-------|-----------------|--------|
| `GOOGLE_CLIENT_ID` | Google Client ID | Final steps [here](#create-oauth-credentials) | Server secret | 
| `GOOGLE_CLIENT_SECRET` | Google Client Secret | Final steps [here](#create-oauth-credentials) | Server secret | 

</details>

<details>
<summary><h2>Fly.io</h2></summary>

Fly.io hosts the MCP server. You'll create an account, install the CLI, create an app, and set the runtime secrets it needs.

### Install the CLI

1. Install `flyctl`: `brew install flyctl` (or see [fly.io/docs/flyctl/install](https://fly.io/docs/flyctl/install/) for other methods)
2. Log in: `fly auth login`

### Create an app

1. Run `fly apps create` and choose a name (e.g. `family-health-mcp`) and region
2. Note the app name — you'll use it for secrets and GitHub Actions

### Set runtime secrets

The MCP server reads environment variables at runtime. Set them on your Fly app:

```bash
fly secrets set \
  DATABASE_URL='your_db_url' \
  GOOGLE_CLIENT_ID='your_google_client_id' \
  GOOGLE_CLIENT_SECRET='your_google_client_secret' \
  MCP_SERVER_URL='https://<your-app-name>.fly.dev' \
  --app <your-app-name>
```

### Create a deploy token

Generate a token for GitHub Actions to deploy on your behalf:

```bash
fly tokens create deploy --app <your-app-name>
```

Save this token — you'll add it as a GitHub Actions secret in the next section.

### Update Google OAuth URIs

After creating the app, go back to your Google Cloud OAuth client and update (if needed):

- **Authorized JavaScript origins:** `https://<your-app-name>.fly.dev`
- **Authorized redirect URIs:** `https://<your-app-name>.fly.dev/auth/callback`

Keep localhost values too if you want to test it locally. 

### Outputs

After completing this step you should have the next values:  

| Key | Value | Where to get it | Purpose | 
|--------|-------|-----------------|--------|
| `FLY_API_TOKEN` | Fly.io deploy token | `fly tokens create deploy --app <your-app-name>` | Github secret |
| `FLY_APP_NAME` | Fly.io app name | Chosen during `fly apps create` | Github secret |

</details>

# Deployment

This section describes how to:
- setup Github repository
- apply database migrations
- seed the data
- deploy MCP server
- try it with your MCP client

### Setup Github repository

1. [Fork this repository](https://github.com/alexzaitsev/family-health/fork) on GitHub
2. In your fork, go to **Settings** → **Secrets and variables** → **Actions** → **New repository secret**
3. Add secrets: `SUPABASE_ACCESS_TOKEN`, `SUPABASE_PROJECT_ID`, `SUPABASE_DB_PASSWORD`, `FLY_API_TOKEN`, `FLY_APP_NAME`.

These secrets are used by the deploy workflow (`.github/workflows/deploy.yml`) to push database migrations and deploy the MCP server on every push to `main`. You can trigger the workflow manually from Actions.

### Apply Supabase migrations and deploy MCP server

Trigger manual `deploy` workflow from Actions. 

### Add family members to Supabase

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

### Give it a try!

Connect the MCP server to your preferred AI client:

**Claude.ai:**

1. Go to [claude.ai](https://claude.ai) → **Left panel** → **Customize** → **Connectors** → **Add custom connector**
2. Enter your server URL: `https://your-production-domain.com/mcp` and give connector the name. Leave advanced settings (OAuth Client ID, OAuth Client Secret) empty
3. Click **Add**
4. Find it in your connectors list and click **Connect** → authenticate with your Google account.

Open new chat and test it. Explicitly tell Claude to use <your-connector-name>.

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