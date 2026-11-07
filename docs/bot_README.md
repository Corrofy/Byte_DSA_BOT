# DSA_DAILY — Discord Bot

A production-grade Discord bot that turns Data Structures & Algorithms (DSA) into a daily habit like Wordle:
- **Three global tracks:** Easy (1 pt), Medium (2 pts), Hard (3 pts)
- **Shared daily problem:** One problem per track per UTC day, released at 00:00 UTC
- **Automated LeetCode verification:** Via public `recentAcSubmissionList` and "About Me" bio code
- **Strict streaks & tie-breaking leaderboards:** Consecutive days per track and overall
- **Copyable daily Wordle-style share card**

---

## Quickstart

### 1. Requirements
- Python 3.12+
- Discord Bot Token with `bot` and `applications.commands` scopes

### 2. Installation
```bash
git clone <repo-url>
cd bot
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Environment Configuration
Create `.env` in the bot root:
```env
DISCORD_TOKEN=your_bot_token_here
OWNER_DISCORD_ID=your_discord_id_here
DATABASE_URL=sqlite+aiosqlite:///./data/dsa_daily.db
LOG_LEVEL=INFO
LEETCODE_GRAPHQL_URL=https://leetcode.com/graphql/
```

### 4. Running the Bot
```bash
python -m bot.main
```

---

## Systemd Service Setup (Ubuntu / Debian / Raspberry Pi)
Copy `bot/dsa_daily.service` to `/etc/systemd/system/dsa_daily.service`:
```bash
sudo cp bot/dsa_daily.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now dsa_daily
sudo systemctl status dsa_daily
```

---

## Discord Slash Commands
- `/help [category]` — Interactive command guide, category filters & Byte's persona lore
- `/usage` — 4-step beginner walkthrough for linking, solving, verifying, and streaks
- `/setup track:<easy|medium|hard> channel:#channel` — Bind channel to difficulty track
- `/settings threads:<on|off> recap-channel:#channel` — Toggle discussion threads & weekly recap
- `/scope set-role role:@role` — Assign bounding Discord role to Byte
- `/scope view` — Inspect active scope configuration and channel command map
- `/scope channel add channel:#chan commands:<group>` — Map command group to a channel
- `/scope channel remove channel:#chan commands:<group>` — Remove command group from channel
- `/scope channel set-config channel:#chan` — Designate private admin/bot channel (`#dsa-config`)
- `/scope channel set-leaderboard channel:#chan` — Designate dedicated leaderboard channel
- `/link username:<leetcode_username>` — Generate bio verification code
- `/link action:verify` — Verify ownership via LeetCode About Me bio
- `/verify track:<easy|medium|hard>` — Verify today's solve
- `/streak` & `/profile [user]` — Check current & longest streaks
- `/leaderboard track:<easy|medium|hard|overall> scope:<global|server>` — View ranks & points
- `/share` — Copy your Wordle-style daily result card
- `/admin_health` — Inspect bot latency and database status
- `/admin_grace date:<YYYY-MM-DD>` — Protect streaks during bot/API outages
- `/test [problem now|solve|status|reset_streak]` — Developer testing commands (when `DEV_MODE=true`, see `docs/DevGuide.md`)

---

## Developer Mode (`DEV_MODE=true`)
To quickly test and run commands without waiting for the 00:00 UTC scheduler, set `DEV_MODE=true` in `bot/.env`. This enables `/test` commands like `/test problem now` (instant daily challenge dispatch into your test channel) and `/test solve`. See **[docs/DevGuide.md](../docs/DevGuide.md)** for full testing workflows and commands.
