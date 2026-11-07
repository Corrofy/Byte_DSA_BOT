# DSA_DAILY — Production Discord Bot

DSA_DAILY is an automated Data Structures and Algorithms habit-building Discord bot. Inspired by Wordle, it delivers one synchronized LeetCode challenge per difficulty track (Easy, Medium, Hard) at 00:00 UTC every day. User solutions are verified against public LeetCode GraphQL records and About Me bio proof codes, updating consecutive-day streaks, server-level collective streaks, and competitive leaderboards.

---

## Repository Structure

```
.
├── bot/                       # Python bot package
│   ├── cogs/                  # Discord slash command modules
│   │   ├── admin.py           # Admin health, manual verification, outage grace days
│   │   ├── daily.py           # Scheduled 00:00 UTC challenge publisher & threads
│   │   ├── dev.py             # Developer testing suite (/test commands)
│   │   ├── help.py            # Command guide, usage routine, Byte persona
│   │   ├── leaderboard.py     # Points boards and Wordle share cards
│   │   ├── linking.py         # LeetCode account linking & bio code verification
│   │   ├── scope.py           # Bot role scoping & channel command isolation
│   │   ├── setup.py           # Track-to-channel binding & server settings
│   │   ├── stats.py           # User streaks, profile cards, role subscriptions
│   │   └── verification.py    # LeetCode GraphQL solve verification engine
│   ├── db/                    # Database models and async session management
│   ├── services/              # Business logic (LeetCode, streaks, problems)
│   ├── ui/                    # Discord embeds and interactive buttons
│   ├── utils/                 # Channel scope guard decorators
│   ├── config.py              # Environment configuration loader
│   ├── dsa_daily.service      # Linux systemd service unit definition
│   ├── main.py                # Bot entry point and startup orchestration
│   └── requirements.txt       # Python package dependencies
├── docs/                      # Complete documentation
│   ├── bot_README.md          # Bot overview and quickstart guide
│   ├── commands.md            # Complete slash command reference
│   ├── Configuration.md       # Bot creation & initial server setup guide
│   ├── ConfigurationGuide.md  # Scope configuration, custom messages & settings
│   ├── CONTRIBUTING.md        # Contribution guidelines and workflow
│   ├── DevGuide.md            # Developer testing guide (/test problem now)
│   ├── FORCONTRIBUTORS.md     # Technical architecture guide for contributors
│   ├── projectSummary.md      # Comprehensive technical specification
│   └── usage.md               # User onboarding & routine walkthrough
├── .env.example               # Environment variable template
└── .gitignore                 # Git ignore rules for Python & SQLite
```

---

## Documentation Links

- [Project Summary](../docs/projectSummary.md): High-level architecture, scoring formulas, and technical specifications.
- [Initial Server Setup](../docs/Configuration.md): Discord Developer Portal bot creation, invite URL generation, and initial channel setup.
- [Command Reference](../docs/commands.md): Complete parameter details and permissions for every slash command.
- [Configuration & Scoping Guide](../docs/ConfigurationGuide.md): Setting up role scoping, channel isolation, custom messages, and outage protection.
- [User Onboarding & Usage Guide](../docs/usage.md): Step-by-step user walkthrough from linking accounts to verifying solves and sharing results.
- [Developer Guide](../docs/DevGuide.md): Local development workflow and instant testing commands with `DEV_MODE=true`.
- [Contributing Guidelines](../docs/CONTRIBUTING.md): Code of conduct, reporting bugs, and pull request standards.
- [Contributor Technical Guide](../docs/FORCONTRIBUTORS.md): Deep dive into subsystems, the streak engine, and coding best practices.

---

## Quickstart

### 1. Prerequisites
- Python 3.12 or higher
- A Discord Bot Application with `bot` and `applications.commands` scopes enabled in the [Discord Developer Portal](https://discord.com/developers/applications)
- Privileged Gateway Intents: **Server Members Intent** enabled

### 2. Local Environment Setup

Navigate to the repository root, create a virtual environment, and install dependencies:

```bash
cd bot
python3 -m venv .venv

# On Linux/macOS:
source .venv/bin/activate

# On Windows (PowerShell):
.venv\Scripts\Activate.ps1

pip install -r requirements.txt
```

### 3. Environment Configuration

Copy the example environment file and fill in your values:

```bash
cp ../.env.example .env
```

Edit `bot/.env`:
```env
# Required Discord bot credentials
DISCORD_TOKEN="YOUR_BOT_TOKEN_FROM_DEVELOPER_PORTAL"
OWNER_DISCORD_ID=123456789012345678

# SQLite WAL mode database path
DATABASE_URL="sqlite+aiosqlite:///./data/dsa_daily.db"

# Optional settings
LOG_LEVEL="INFO"
LEETCODE_GRAPHQL_URL="https://leetcode.com/graphql/"
LEETCODE_USER_AGENT="DSA_DAILY/1.0 (Discord Bot)"
DAILY_POST_HOUR_UTC=0
RECAP_HOUR_UTC=18

# Developer Mode (Enables instant /test commands and 1-second guild syncing)
DEV_MODE=false
DEV_GUILD_ID=123456789012345678
```

### 4. Running the Bot

```bash
python -m bot.main
```

Upon successful startup, the bot connects to the Discord Gateway, synchronizes application slash commands, and begins the daily 00:00 UTC scheduler.

---

## Production Deployment (Systemd)

To keep the bot running 24/7 on a Linux server, VPS, or Raspberry Pi, use the included systemd service unit:

1. Update the paths and user in `bot/dsa_daily.service` to match your environment.
2. Copy the service unit to systemd:
   ```bash
   sudo cp bot/dsa_daily.service /etc/systemd/system/dsa_daily.service
   sudo systemctl daemon-reload
   sudo systemctl enable --now dsa_daily
   sudo systemctl status dsa_daily
   ```

---

## Discord Server Channel Setup & Scoping

1. In your Discord server, create the recommended channels:
   - Category: `DSA_DAILY`
     - `#dsa-easy`
     - `#dsa-medium`
     - `#dsa-hard`
     - `#dsa-leaderboard`
     - `#dsa-config` *(Private: visible only to Admins/Moderators and the bot)*
2. Assign the bot scope role and designate channels:
   ```text
   /scope set-role role:@dsaBot
   /scope channel set-config channel:#dsa-config
   /scope channel set-leaderboard channel:#dsa-leaderboard
   ```
3. Map track solver commands to channels:
   ```text
   /scope channel add channel:#dsa-easy commands:dsa_track
   /scope channel add channel:#dsa-medium commands:dsa_track
   /scope channel add channel:#dsa-hard commands:dsa_track
   ```
4. Bind difficulty tracks to channels (run from `#dsa-config`):
   ```text
   /setup track:easy channel:#dsa-easy
   /setup track:medium channel:#dsa-medium
   /setup track:hard channel:#dsa-hard
   ```
5. Enable discussion threads and recap:
   ```text
   /settings threads:on recap-channel:#dsa-leaderboard show_solvers:on
   ```

---

## Primary Slash Commands

### Solver Commands
- `/link username:<leetcode_handle>`: Generate verification code for your LeetCode About Me bio.
- `/link action:verify`: Verify profile ownership and link your account.
- `/verify track:<easy|medium|hard>`: Verify today's solve on LeetCode.
- `/share`: Generate Wordle-style copyable daily result card.
- `/streak`: View current active streak and personal record.
- `/profile [user]`: Comprehensive statistics card and language breakdown.
- `/subscribe track:<easy|medium|hard>`: Self-assign daily notification ping role.
- `/unsubscribe track:<track>`: Remove notification ping role.
- `/help`: Categorized command manual and persona backstory.
- `/usage`: Step-by-step 4-stage onboarding routine.

### Leaderboard & Stats
- `/leaderboard [track:overall|easy|medium|hard] [scope:server|global]`: Community standings, score rankings, and Server Collective Streak banner.
- `/privacy [leaderboard:true|false] [leetcode:true|false]`: Configure visibility on public leaderboards.

### Server Administration & Scoping
- `/scope set-role role:@role`: Assign bounding Discord role to the bot.
- `/scope view`: Display active server scope configuration and channel command map.
- `/scope channel add channel:#chan commands:<dsa_track|leaderboard|config|all>`: Map command group to channel.
- `/scope channel remove channel:#chan commands:<group>`: Remove command group from channel.
- `/scope channel set-config channel:#chan`: Designate private configuration channel (`#dsa-config`).
- `/scope channel set-leaderboard channel:#chan`: Designate leaderboard channel (`#dsa-leaderboard`).
- `/setup track:<track> channel:#chan`: Bind channel to difficulty track.
- `/settings threads:<on|off> recap-channel:#chan show_solvers:<on|off>`: Server-level settings.
- `/admin_health`: Bot latency, gateway health, and database connection status.
- `/admin_grace date:<YYYY-MM-DD>`: Protect streaks during LeetCode/bot outages.

### Developer Commands (`DEV_MODE=true`)
- `/test problem now [track:easy|medium|hard]`: Instantly publish a challenge embed.
- `/test solve [track:easy|medium|hard]`: Simulate an accepted solve for testing streak increments.
- `/test reset_streak`: Clear user streaks to verify reset and recovery behavior.
- `/test status`: Inspect real-time developer flags, active SQLite database, and clock state.
