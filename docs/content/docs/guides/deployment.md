---
title: Deployment
description: Set up the Github repository, apply migrations, seed data, and deploy the MCP server.
---

After completing the [prerequisites](/guides/prerequisites/), you are ready to deploy Protocol.

## Setup Github repository

1. [Fork this repository](https://github.com/alexzaitsev/protocol/fork) on GitHub
2. In your fork, go to **Settings** → **Secrets and variables** → **Actions** → **New repository secret**
3. Add secrets: `SUPABASE_ACCESS_TOKEN`, `SUPABASE_PROJECT_ID`, `SUPABASE_DB_PASSWORD`, `FLY_API_TOKEN`, `FLY_APP_NAME`.

These secrets are used by the deploy workflow (`.github/workflows/deploy.yml`) to push database migrations and deploy the MCP server. You can trigger the workflow manually from Actions.

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

- **`id`** - a short text slug used throughout the system (e.g. `jane`)
- **`google_email`** - must match the Google account used to sign in via OAuth
- **`sex`** - `m` or `f`
- `health_profiles` and `preferences` rows are required - defaults are fine to start, update them later

To remove a user, delete their row from `person.users` - all user-specific rows (`health_profiles`, `preferences`) are removed automatically via cascading deletes. Shared tables are left intact.

Once users are added, proceed to [Onboarding](/guides/onboarding/) to connect an MCP client and set up health profiles.

## Set preferred timezone in Supabase

This is an optional step, needed for correct start/end date in `supplements` and other tables. You can skip it if UTC timestamps are OK. This sets the timezone for entire database (all users).

1. Find your timezone name in [this list](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones).
2. Go to **Supabase Dashboard** → your project → **SQL Editor** and run:

```sql
ALTER DATABASE postgres SET timezone = 'America/New_York';
```

Replace `America/New_York` with your timezone.

---

Once deployed, proceed to [Onboarding](/guides/onboarding/) to connect your AI client and set up health profiles.
