---
title: Onboarding
description: Connect an MCP client to the Protocol server and set up your health profile.
---

This guide assumes Claude.ai as the MCP client, but the steps apply to any client that supports streamable HTTP transport with OAuth - use your server URL `https://your-production-domain.com/mcp` wherever a connection URL is required.

## Connect to MCP server

1. Go to [claude.ai](https://claude.ai) → **Left panel** → **Customize** → **Connectors** → **Add custom connector**
2. Enter your server URL and give the connector a name. Leave advanced settings (OAuth Client ID, OAuth Client Secret) empty
3. Click **Add**
4. Find it in your connectors list and click **Connect** → authenticate with your Google account

## Set up project prompt

1. Create a new Claude project
2. Paste the [project prompt](https://github.com/alexzaitsev/protocol/blob/main/prompts/project_prompt.md) into the project instructions
3. Modify the first lines to match your `<connector-name>` so Claude can correctly identify the connector
4. Open a new chat in the project and test it

## Initial onboarding

Paste the [onboarding prompt](https://github.com/alexzaitsev/protocol/blob/main/prompts/onboarding_prompt.md) into Claude to set up your health profile and preferences. Claude will ask you questions conversationally and save the answers using the Protocol tools.

Once done, see [Usage Examples](/guides/usage-examples/) for prompts to get started.
