---
title: Fly.io
description: Host the MCP server.
---

Fly.io hosts the MCP server. You'll create an account, install the CLI, create an app, and set the runtime secrets it needs.

## Install the CLI

1. Install `flyctl`: `brew install flyctl` (or see [fly.io/docs/flyctl/install](https://fly.io/docs/flyctl/install/) for other methods)
2. Log in: `fly auth login`

## Create an app

1. Run `fly apps create` and choose a name (e.g. `protocol-mcp`) and region
2. Note the app name - you'll use it for secrets and GitHub Actions

## Set runtime secrets

The MCP server reads environment variables at runtime. Set them on your Fly app:

```bash
fly secrets set \
  DATABASE_URL='your_db_url' \
  GOOGLE_CLIENT_ID='your_google_client_id' \
  GOOGLE_CLIENT_SECRET='your_google_client_secret' \
  MCP_SERVER_URL='https://<your-app-name>.fly.dev' \
  --app <your-app-name>
```

## Machine configuration

`fly.toml` is pre-configured with `min_machines_running = 1` and `auto_stop_machines = 'suspend'`. This keeps one machine always running so there are no cold starts - the Anthropic MCP proxy has a short connection timeout, and a suspended machine takes 5–8 seconds to wake up, causing 502 errors before the server is ready.

With a single shared-1x-512mb machine running 24/7, expect roughly $3-4/month. Use the [Fly.io pricing calculator](https://fly.io/calculator?f=c&b=sjc.1&a=no_none&m=0_0_0_0_0&r=shared_0_1_ord&t=10_100_5&u=0_1_100&g=1_shared_730_1_512_sjc_0_0) to estimate cost for your region and machine size.

**Fly.io waives monthly bills under $5**, so this setup is effectively free.

## Create a deploy token

Generate a token for GitHub Actions to deploy on your behalf:

```bash
fly tokens create deploy --app <your-app-name>
```

Save this token - you'll add it as a GitHub Actions secret in the next section.

## Update Google OAuth URIs

After creating the app, go back to your Google Cloud OAuth client and update (if needed):

- **Authorized JavaScript origins:** `https://<your-app-name>.fly.dev`
- **Authorized redirect URIs:** `https://<your-app-name>.fly.dev/auth/callback`

Keep localhost values too if you want to test it locally.

## Outputs

After completing this step you should have the next values:

| Key | Value | Where to get it | Purpose |
|--------|-------|-----------------|--------|
| `FLY_API_TOKEN` | Fly.io deploy token | `fly tokens create deploy --app <your-app-name>` | Github secret |
| `FLY_APP_NAME` | Fly.io app name | Chosen during `fly apps create` | Github secret |
