# DSA_DAILY — Developer & Testing Guide (DevGuide)

This guide provides developers with instructions to quickly run, test, and iterate on **DSA_DAILY** without waiting for the scheduled 00:00 UTC daily cron or needing paid infrastructure.

By enabling **`DEV_MODE = true`**, developer-specific testing slash commands such as `/test` and `/test problem now` become available for rapid end-to-end verification.

---

## 1. Quickstart (Under 3 Minutes)

### Step 1: Install Dependencies
Ensure you have Python 3.12+ installed, then create and activate a virtual environment:

```bash
cd bot
python3 -m venv .venv

# On Linux/macOS:
source .venv/bin/activate

# On Windows (PowerShell):
.venv\Scripts\Activate.ps1

pip install -r requirements.txt
```

### Step 2: Configure `.env` with `DEV_MODE=true`
Create or edit `bot/.env`:

```env
# Discord Bot Credentials
DISCORD_TOKEN="YOUR_BOT_TOKEN_FROM_DEVELOPER_PORTAL"
OWNER_DISCORD_ID=123456789012345678

# --- Developer Mode Configuration ---
DEV_MODE="true"

# (Optional but Recommended) Target test server ID for instant 0-second slash command syncing
DEV_GUILD_ID=123456789012345678

# Local Database
DATABASE_URL="sqlite+aiosqlite:///./data/dsa_daily_dev.db"
LOG_LEVEL="DEBUG"
```

> **Why set `DEV_GUILD_ID`?**  
> Discord's global application command sync can take up to 60 minutes to propagate across servers. Providing `DEV_GUILD_ID` forces the bot to immediately sync commands to your development server on startup in **under 1 second**.

### Step 3: Run the Bot
```bash
python -m bot.main
```

When started with `DEV_MODE=true`, you will see:
```text
INFO:dsa_daily:Loaded cog: bot.cogs.dev
INFO:dsa_daily:Logged in as Byte (ID: 990123456789)
INFO:dsa_daily:🧪 DEV_MODE is ENABLED! /test commands (/test problem now, /test solve, /test status) are active.
INFO:dsa_daily:Fast-synced 15 slash commands directly to dev guild 123456789012345678.
```

---

## 2. Developer Slash Commands Reference (`/test`)

When `DEV_MODE = true`, the `/test` command group is registered in Discord and within the Discord Simulator.

### 1. `/test problem now`
Forces immediate generation and posting of a daily challenge into the current channel, bypassing the 00:00 UTC scheduler and idempotency locks.

- **Options**:
  - `action`: `now` (default) dispatches directly to the channel; `preview` returns an ephemeral preview only you can see.
  - `track`: `easy` (default), `medium`, or `hard`.
- **What it tests**:
  - Challenge retrieval from the problem pool (or live LeetCode).
  - Embed styling (difficulty color accents, topic tags, challenge number).
  - Wordle-style solver presence section (`show_solvers`).
  - Interactive buttons (`[Verify my solve]` and `[Share result]`).
  - Automatic thread discussion creation (`#DSA #[num] — Track`).
- **Example**:
  ```text
  /test problem action:now track:medium
  ```

---

### 2. `/test status`
Displays live developer mode diagnostics, environment flags, database connectivity, and registered tracks.

- **Options**: None (ephemeral)
- **Output details**:
  - `DEV_MODE` status
  - Current UTC timestamp and hour
  - Discord Gateway latency in milliseconds
  - Database URL and SQLite WAL status
  - Counts of active tracks, daily challenges, users, and recorded solves

---

### 3. `/test solve`
Simulates an accepted LeetCode submission for a user and track, instantly crediting the solve without waiting for the public LeetCode GraphQL API.

- **Options**:
  - `track`: `easy`, `medium`, or `hard`.
  - `user` *(optional)*: Discord member to credit (defaults to yourself).
  - `language` *(optional)*: Language string (defaults to `Python3`).
- **What it tests**:
  - Streak engine incrementing (`current` streak and `longest` streak).
  - Overall point tally updates (Easy = 1 pt, Medium = 2 pts, Hard = 3 pts).
  - Live leaderboard re-ranking.
- **Example**:
  ```text
  /test solve track:easy language:Rust
  ```

---

### 4. `/test reset_streak`
Clears streak records for a user so you can test broken streak behavior and new streak resets without modifying the database by hand.

- **Options**:
  - `user` *(optional)*: Discord member whose streaks to reset (defaults to yourself).
- **Example**:
  ```text
  /test reset_streak
  ```

---

## 3. Fast Testing in the Discord Simulator UI

If you don't have a Discord Bot token configured, you can test all developer workflows directly inside the **Web Discord Simulator**:

1. Open the **Discord Simulator** tab in the application.
2. Ensure the top-right **DEV_MODE** badge is toggled **ON** (active by default).
3. Type `/test problem now` into the message input and press Enter:
   - A fresh test challenge is immediately posted to the active channel.
   - Interactive `[Verify my solve]` and `[Share result]` buttons are fully wired up.
4. Type `/test solve track:easy` or click **[Verify my solve]** to simulate solving today's problem.
5. Use the **Time Machine** bar at the top to fast-forward UTC days and test streak continuity across consecutive days!

---

## 4. Running Automated Tests

The codebase includes an async test suite using `pytest` and `respx` (for mocking LeetCode GraphQL calls):

```bash
# Run full test suite
pytest -v

# Run with stdout logging
pytest -v -s

# Run specific streak computation tests
pytest tests/test_streaks.py -v
```

---

## 5. Development Environment Variables

| Variable | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `DEV_MODE` | Boolean | `false` | Enables `/test` command group and dev endpoints |
| `DEV_GUILD_ID` | Integer | `None` | Target guild for 0-second slash command syncing |
| `DISCORD_TOKEN` | String | `""` | Bot token from Discord Developer Portal |
| `OWNER_DISCORD_ID` | Integer | `0` | Your Discord ID for owner commands (`/admin_grace`) |
| `DATABASE_URL` | String | `sqlite+aiosqlite:///./data/dsa_daily.db` | Async SQLAlchemy database URI |
| `LOG_LEVEL` | String | `INFO` | Set to `DEBUG` for verbose SQL and gateway logs |
| `DAILY_POST_HOUR_UTC`| Integer | `0` | UTC hour for daily challenge dispatch (0 = midnight) |
| `RECAP_HOUR_UTC` | Integer | `18` | UTC hour for Sunday weekly recap |

---

## 6. Troubleshooting Common Developer Issues

### Issue 1: Slash commands not showing in Discord
- **Cause**: Discord global slash command sync takes up to 1 hour to propagate.
- **Solution**: Set `DEV_GUILD_ID="YOUR_SERVER_ID"` in `bot/.env` and restart. Commands will appear in your server instantly.

### Issue 2: `[DEV_MODE is disabled]` error when running `/test`
- **Cause**: `DEV_MODE` is unset or `false`.
- **Solution**: Set `DEV_MODE=true` in `bot/.env` and restart the bot process.

### Issue 3: LeetCode profile returns 404 or private
- **Cause**: The user hasn't set their LeetCode profile privacy to public or recently changed handles.
- **Solution**: During development, use `/test solve track:easy` to bypass the LeetCode API and test internal logic directly.

### Issue 4: Resetting the test database
- To start with a clean state, delete the local SQLite file:
  ```bash
  rm data/dsa_daily_dev.db*
  ```
  The bot will automatically re-run `init_db()` and seed the default tracks upon startup.
