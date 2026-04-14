---
title: Supabase
description: Set up the PostgreSQL database and connection URL.
---

Supabase provides the PostgreSQL database. You'll set up a project and construct a connection URL that the MCP server uses at runtime.

## Create a project

1. Go to [supabase.com/dashboard](https://supabase.com/dashboard) and create an account
2. Click **New Project**, choose an organization, set a project name, database password, and region
3. Note the **Project Reference ID** from the project URL: `https://supabase.com/dashboard/project/<project-ref>`

## Enforce SSL

For extra security it's recommended to enable "Enforce SSL on incoming connections" setting.
It can be found using next link: `https://supabase.com/dashboard/project/<project-ref>/database/settings#ssl-configuration`

## Construct the connection URL

The MCP server connects via asyncpg using a `DATABASE_URL` environment variable. Build it from your Supabase dashboard:

1. Go to **Connect** → **Connection String** → **Transaction pooler** (port `6543`)
2. The URL follows this format:

```
postgresql://postgres.<project-ref>:<password>@<pooler-host>:6543/postgres?sslmode=verify-full
```

- **`<pooler-host>`** - copy the host from the transaction pooler connection string
- **`<password>`** - your database password, URL-encoded (special characters like `@`, `!`, `#`, `%` must be escaped, e.g. `p@ss!` → `p%40ss%21`)

## Outputs

After completing this step you should have the next values:

| Key | Value | Where to get it | Purpose |
|--------|-------|-----------------|--------|
| `SUPABASE_ACCESS_TOKEN` | Supabase personal access token | [supabase.com/dashboard/account/tokens](https://supabase.com/dashboard/account/tokens) | Github secret |
| `SUPABASE_PROJECT_ID` | Project reference ID | From the project URL: `supabase.com/dashboard/project/<project-ref>` | Github secret |
| `SUPABASE_DB_PASSWORD` | Database password | Set during [project creation](#create-a-project) | Github secret |
| `DATABASE_URL` | Connection URL | See [here](#construct-the-connection-url) | Server secret |
