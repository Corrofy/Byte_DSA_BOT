# DSA_DAILY — Configuration, Testing & Deployment Guide

This document provides a complete guide for setting up, testing, and deploying **DSA_DAILY** using your own Discord server and bot token, with **zero paid hosting required**.

---

## 1. Prerequisites

1. **Python 3.12+** installed on your computer:
   ```bash
   python3 --version
   ```
2. **Discord Account** with ownership or `Manage Server` permissions on your test Discord server.
3. **Discord Developer Portal Access** (free at [discord.com/developers](https://discord.com/developers/applications)).

---

## 2. Creating Your Discord Bot Application

1. Visit [https://discord.com/developers/applications](https://discord.com/developers/applications) and click **"New Application"**.
2. Name your bot (e.g. `DSA_DAILY` or `Byte`).
3. In the left navigation, click **Bot**:
   - Under **Privileged Gateway Intents**, enable:
     - **Server Members Intent** (checked)
   - Click **Reset Token** and copy your **Bot Token**. Save this securely (never share or commit this token).
4. In the left navigation, click **OAuth2 ➔ URL Generator**:
   - Under **Scopes**, select:
     - `bot`
     - `applications.commands`
   - Under **Bot Permissions**, select:
     - `View Channels`
     - `Send Messages`
     - `Embed Links`
     - `Attach Files`
     - `Read Message History`
     - `Create Public Threads`
     - `Send Messages in Threads`
     - `Manage Roles`
5. Copy the generated invite URL at the bottom, paste it into your browser, and authorize the bot to join your Discord server.

---

## 3. Local Setup & Testing (No Cloud Hosting Needed)

You can run the bot directly on your laptop/desktop computer while testing with your Discord server.

### Step 1: Clone or Navigate to the Bot Folder
```bash
cd /path/to/project/bot
```

### Step 2: Create a Virtual Environment
```bash
python3 -m venv .venv

# On Linux/macOS:
source .venv/bin/activate

# On Windows (PowerShell):
.venv\Scripts\Activate.ps1
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables
Create a file named `.env` in the `bot` folder:
```env
# Required: Paste your bot token from the Discord Developer Portal
DISCORD_TOKEN="YOUR_BOT_TOKEN_HERE"

# Required: Your own Discord User ID (Enable Developer Mode in Discord -> Right click your avatar -> Copy User ID)
OWNER_DISCORD_ID=123456789012345678

# SQLite WAL mode database (stored locally in ./data/)
DATABASE_URL="sqlite+aiosqlite:///./data/dsa_daily.db"

# Optional settings
LOG_LEVEL="INFO"
LEETCODE_GRAPHQL_URL="https://leetcode.com/graphql/"
LEETCODE_USER_AGENT="DSA_DAILY/1.0"
DAILY_POST_HOUR_UTC=0
RECAP_HOUR_UTC=18
```

### Step 5: Start the Bot
```bash
python -m bot.main
```
You should see output similar to:
```text
INFO:dsa_daily:Loaded cog: bot.cogs.setup
INFO:dsa_daily:Loaded cog: bot.cogs.daily
INFO:dsa_daily:Loaded cog: bot.cogs.linking
INFO:dsa_daily:Loaded cog: bot.cogs.verification
INFO:dsa_daily:Loaded cog: bot.cogs.stats
INFO:dsa_daily:Loaded cog: bot.cogs.leaderboard
INFO:dsa_daily:Loaded cog: bot.cogs.admin
INFO:dsa_daily:Loaded cog: bot.cogs.help
INFO:dsa_daily:Logged in as Byte (ID: 990123456789)
INFO:dsa_daily:Synced 12 application slash commands.
```

---

## 4. Initial Server Setup on Discord

Once your bot is online in your Discord server:

1. Create text channels in your server (recommended structure):
   - Category: `DSA_DAILY`
     - `#dsa-easy`
     - `#dsa-medium`
     - `#dsa-hard`
     - `#dsa-leaderboard`
     - `#dsa-config` *(Private: visible only to Admins/Mods & Byte)*
2. Assign the bot scope role and designate channels:
   ```text
   /scope set-role role:@dsaBot
   /scope channel set-config channel:#dsa-config
   /scope channel set-leaderboard channel:#dsa-leaderboard
   ```
3. Map track commands to channels:
   ```text
   /scope channel add channel:#dsa-easy commands:dsa_track
   /scope channel add channel:#dsa-medium commands:dsa_track
   /scope channel add channel:#dsa-hard commands:dsa_track
   ```
4. Run the setup slash commands (in `#dsa-config`):
   ```text
   /setup track:easy channel:#dsa-easy
   /setup track:medium channel:#dsa-medium
   /setup track:hard channel:#dsa-hard
   ```
5. Enable spoiler discussion threads:
   ```text
   /settings threads:on recap-channel:#dsa-leaderboard
   ```
6. Verify your own LeetCode account:
   ```text
   /link username:<your_leetcode_username>
   ```
   Paste the code into your LeetCode profile "About Me" bio, then run:
   ```text
   /link action:verify
   ```

---

## 5. Deployment Options (Zero Cost)

When you are ready to keep the bot online 24/7 without keeping your computer on:

### Option A: Friend's Home Server / Old Laptop / Raspberry Pi (Recommended)
- **Why**: Residential IP (unlikely to get rate-limited by LeetCode), persistent disk, zero cost.
- **Setup**: Install Python 3.12, copy the `bot` folder, configure systemd using `bot/dsa_daily.service`:
  ```bash
  sudo cp bot/dsa_daily.service /etc/systemd/system/dsa_daily.service
  sudo systemctl daemon-reload
  sudo systemctl enable --now dsa_daily
  sudo systemctl status dsa_daily
  ```

### Option B: Free Always-On VPS (Oracle Cloud Free Tier / Google Cloud e2-micro)
- Oracle Cloud offers an Always Free ARM instance with 4 OCPUs and 24GB RAM.
- Follow the same steps as Option A.

---

## 6. Verifying Health & Backups

- Run `/admin_health` to check Discord Gateway latency and active SQLite database status.
- Automated SQLite database backups are stored in `./backups/` using `sqlite3 .backup`.
