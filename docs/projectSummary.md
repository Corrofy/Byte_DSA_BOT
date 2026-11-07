# DSA_DAILY Project Summary

## 1. Executive Summary

DSA_DAILY is an automated Data Structures and Algorithms (DSA) habit-building platform centered around a production Discord bot named "Byte", accompanied by an interactive browser-based simulation studio. 

Inspired by daily habit mechanics like Wordle, DSA_DAILY delivers one synchronized challenge per track (Easy, Medium, Hard) at 00:00 UTC each day. Member solves are automatically validated against public LeetCode GraphQL submission records and "About Me" bio proofs, driving consecutive-day streaks, server-level collective streaks, and competitive leaderboards.

---

## 2. Core Architecture

The repository contains two operational layers:
1. **Discord Bot Backend (Python 3.12+)**: The production service built with `discord.py`, SQLAlchemy (asyncio with SQLite WAL mode), and an asynchronous LeetCode GraphQL client.
2. **Interactive Simulation Studio (TypeScript / React / Vite)**: A browser-based Discord and LeetCode simulator that models the bot's end-to-end user workflows, time progression, administrative controls, and problem dispatching without requiring live Discord bot credentials.

### Directory Structure
```
dsa_bot_v2/
├── bot/                       # Python bot application
│   ├── cogs/                  # Modular slash command cogs
│   │   ├── admin.py           # Health, manual verifications, outage grace days
│   │   ├── daily.py           # Automated 00:00 UTC scheduler & embed publisher
│   │   ├── dev.py             # Developer test suite (/test commands)
│   │   ├── help.py            # Command guide, usage routine, persona dialogue
│   │   ├── leaderboard.py     # Points standings & Wordle-style share cards
│   │   ├── linking.py         # LeetCode bio code verification flow
│   │   ├── scope.py           # Channel scoping & role-based access control
│   │   ├── setup.py           # Channel-to-track binding & server settings
│   │   ├── stats.py           # Streak metrics, profile summaries, subscriptions
│   │   └── verification.py    # LeetCode GraphQL solve verification engine
│   ├── db/                    # Database models and session management
│   ├── services/              # Business logic (LeetCode, streaks, problems)
│   ├── ui/                    # Discord embeds and component buttons
│   ├── utils/                 # Utility guards (scope verification)
│   ├── config.py              # Pydantic configuration loader
│   ├── dsa_daily.service      # Systemd service unit definition
│   └── main.py                # Bot startup and cog registration
├── docs/                      # Architectural and operational documentation
│   ├── commands.md            # Complete slash command reference
│   ├── Configuration.md       # Bot application creation and setup guide
│   ├── ConfigurationGuide.md  # Customizations, messages, and role scoping
│   ├── DevGuide.md            # Developer mode (/test) documentation
│   └── usage.md               # User onboarding walkthrough
├── src/                       # TypeScript / React web simulation studio
│   ├── components/            # UI modals and Discord simulator interface
│   ├── data/                  # Seed problems (Blind 75, NeetCode 150)
│   ├── store/                 # Global state management and action handlers
│   └── types/                 # Domain interfaces and type definitions
├── server.ts                  # Local Express/Vite proxy server
└── package.json               # Frontend dependencies and scripts
```

---

## 3. Key Features

### 3.1. Track Structure and Scoring
- **Easy Track**: 1 point per solve.
- **Medium Track**: 2 points per solve.
- **Hard Track**: 3 points per solve.
- **Tie-Breaking Formula**:
  - Overall Board: Total Points -> Total Solves -> Current Streak.
  - Track Boards: Current Streak -> Longest Streak -> Total Solves.

### 3.2. Account Linking & Zero-Password Verification
- Member runs `/link username:<leetcode_handle>`.
- Bot generates a temporary, cryptographically secure code token (e.g., `DSA_DAILY-8F2B1C`) valid for 10 minutes.
- The member pastes the code into their public LeetCode profile "About Me" bio.
- Member runs `/link action:verify`. The bot queries LeetCode GraphQL, validates code presence, and permanently binds the Discord ID to the LeetCode handle.

### 3.3. Daily Solve Verification
- Members click the `[Verify my solve]` button on the challenge embed or invoke `/verify track:<track>`.
- The bot queries LeetCode's public `recentAcSubmissionList` GraphQL API.
- The submission must match the challenge slug, have status `Accepted`, and fall within the UTC challenge date window.
- Solves increment the member's track streak and overall streak.

### 3.4. Server Collective Streaks & Solver Presence Cards
- **Server Collective Streak**: Increments daily if at least one server member logs an accepted solve on that UTC date.
- **Solver Presence Card**: The daily post displays plain-text solver names with streak counters directly within the embed. To protect server members from notification spam, display names are used without pinging `<@user_id>` tags.

### 3.5. Outage Grace Days
- If the LeetCode API or host machine suffers an outage, the bot owner can execute `/admin_grace date:<YYYY-MM-DD> reason:<reason>`.
- The streak computation engine treats that calendar date as solved across all users, preserving consecutive streak continuity without awarding artificial points or solve counts.

---

## 4. Role-Based Scoping & Channel Isolation

Administrators can strictly govern where the bot can operate and which commands can be executed in specific channels.

### 4.1. Access Bounding via Discord Roles
- The administrator assigns the bot a specific Discord role (e.g., `@dsaBot`).
- Discord permission overwrites on channels and categories dictate the bot's reading and writing scope.
- The administrator links the role inside the bot using `/scope set-role role:@dsaBot`.

### 4.2. Command Group Routing
Commands are categorized into distinct groups:
- **`dsa_track`**: Solver commands (`/verify`, `/link`, `/unlink`, `/subscribe`, `/unsubscribe`, `/share`, `/profile`, `/streak`, `/help`, `/usage`).
- **`leaderboard`**: `/leaderboard`.
- **`config`**: Administrative commands (`/setup`, `/settings`, `/setmessage*`, `/admin_*`, `/scope`).
- **`all`**: Unrestricted permission.

### 4.3. Channel Configuration Rules
- **Private Configuration Channel**: Designated via `/scope channel set-config channel:#dsa-config`. Only admins, moderators, and the bot have access; administrative commands are restricted here.
- **Dedicated Leaderboard Channel**: Designated via `/scope channel set-leaderboard channel:#dsa-leaderboard`.
- **Track Channels**: Assigned `dsa_track` permissions via `/scope channel add channel:<#channel> commands:dsa_track`.
- **Scope Enforcement**: If a user runs a command outside its permitted channel, the bot replies with an ephemeral message directing them to the authorized channel.

---

## 5. Developer Mode (`DEV_MODE = true`)

Setting `DEV_MODE=true` in the environment unlocks developer tools:
- Instant slash command synchronization to a development guild using `DEV_GUILD_ID` in under one second.
- `/test problem now`: Dispatches a daily challenge immediately without waiting for the 00:00 UTC schedule.
- `/test solve`: Simulates an accepted solve for a user and track to test streak increments.
- `/test reset_streak`: Clears streak records to test zero-streak and recovery conditions.
- `/test status`: Displays system clock, active SQLite WAL database, and registered challenge metrics.

---

## 6. Technology Stack

- **Language**: Python 3.12+ (Bot), TypeScript / React 18 (Simulation Studio)
- **Framework**: `discord.py` 2.3+
- **Database**: SQLite 3 with Write-Ahead Logging (WAL) via SQLAlchemy (asyncio) and `aiosqlite`
- **External API**: LeetCode GraphQL (`https://leetcode.com/graphql/`)
- **Frontend Tooling**: Vite, Tailwind CSS, Lucide Icons, Canvas Confetti
- **Deployment**: Systemd service unit (`dsa_daily.service`) for Linux VPS, Raspberry Pi, or home server deployment.
