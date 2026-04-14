---
title: Google Cloud
description: Configure OAuth 2.0 for user authentication.
---

Google Cloud provides OAuth 2.0 for user authentication. Since this is a family-scoped project, the app stays in **Testing** mode - there is no need for publishing.

## Create a project

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Click the project dropdown → **New Project**
3. Enter a name (e.g. "Protocol MCP") → **Create**

## Configure OAuth consent

Google has renamed "OAuth consent screen" to **Google Auth Platform**. Navigate to **Menu → Google Auth Platform** (or the legacy path *APIs & Services → OAuth consent screen*, which redirects).

1. Click **Get Started**
2. **App Information**: enter app name, select support email → **Next**
3. **Audience**: choose **External** → **Next**
4. **Contact Information**: enter notification email → **Next**
5. **Agree** to terms → **Create**

After creation:

6. Go to **Audience** → keep **Testing** status (limits to 100 test users)
7. Under **Test users**, click **Add users** → add family member email addresses
8. Go to **Data Access** → **Add or Remove Scopes** → add `openid` and `email` (both non-sensitive) → **Update** → **Save**

## Create OAuth credentials

Navigate to **Google Auth Platform → Clients** (or legacy *APIs & Services → Credentials*).

1. Click **Create Client** (or *Create Credentials → OAuth client ID*)
2. Application type: **Web application**
3. Name: anything (e.g. "Protocol MCP")
4. Under **Authorized JavaScript origins**, add your server's base URL (e.g. `https://your-production-domain.com`)
5. Under **Authorized redirect URIs**, add your server's callback URL: `https://your-production-domain.com/auth/callback`
6. Click **Create**
7. Copy the **Client ID** and **Client Secret** - store them securely

**Local development (optional):** To run the server locally, add these to the same OAuth client:

- **Authorized JavaScript origins:** `http://localhost:8000`
- **Authorized redirect URIs:** `http://localhost:8000/auth/callback`

Google allows multiple origins and redirect URIs per client, so both local and production can coexist.

## Outputs

After completing this step you should have the next values:

| Key | Value | Where to get it | Purpose |
|--------|-------|-----------------|--------|
| `GOOGLE_CLIENT_ID` | Google Client ID | Final steps [here](#create-oauth-credentials) | Server secret |
| `GOOGLE_CLIENT_SECRET` | Google Client Secret | Final steps [here](#create-oauth-credentials) | Server secret |
