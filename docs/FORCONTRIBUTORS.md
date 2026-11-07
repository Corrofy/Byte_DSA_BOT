# Guide for Contributors (FORCONTRIBUTORS)

This guide provides technical onboarding, architectural details, and developer guidelines for engineers contributing to the DSA_DAILY codebase.

---

## 1. Project Architecture Overview

DSA_DAILY is structured into decoupled modules designed for maintainability and scalability:

```
bot/
├── cogs/          # Discord application command handlers (cogs)
├── db/            # Database engine, async session factory, SQLAlchemy models
├── services/      # Core business domains (LeetCode API, streaks, leaderboards)
├── ui/            # Discord UI elements (embed formatting, buttons, views)
├── utils/         # Cross-cutting concerns (channel scoping guards)
├── config.py      # Environment variables and settings validation
└── main.py        # Bot instance, gateway intents, and startup orchestration
```

### Key Principles
- **Cog Modularity**: Every domain is isolated into its own cog (`setup`, `daily`, `linking`, `verification`, `stats`, `leaderboard`, `admin`, `help`, `scope`, `dev`). New commands should be added to the relevant domain cog rather than expanding monolithic files.
- **Service Layering**: Command handlers in `cogs/` handle Discord interactions and validation, then delegate data operations and calculations to `services/`.
- **Database Safety**: Database interactions use SQLite in Write-Ahead Logging (WAL) mode via SQLAlchemy async sessions. Always use `async with async_session() as session:` context managers.

---

## 2. Core Subsystems

### 2.1. Challenge Dispatching (`bot/cogs/daily.py` & `bot/services/problems.py`)
- Scheduled challenges execute at 00:00 UTC daily.
- Problem rotation applies a 90-day cooldown algorithm to prevent duplicate problems from appearing within 3 months.
- Idempotency is enforced: if a challenge is already published for `(challenge_date, track_id)`, duplicate dispatches are rejected.

### 2.2. LeetCode GraphQL Client (`bot/services/leetcode.py`)
- Interacts with `https://leetcode.com/graphql/`.
- Uses custom User-Agent headers to avoid standard rate-limiting.
- Queries `recentAcSubmissionList` to retrieve verified solves and `matchedUser` for bio code verification.
- Always handle network timeouts, rate limit responses (HTTP 429), and GraphQL payload errors gracefully.

### 2.3. Streak Engine (`bot/services/streaks.py`)
- Evaluates consecutive challenge days per track (`easy`, `medium`, `hard`) and overall.
- Outage grace days registered in `outage_grace_days` table are treated as solved days to prevent streak breaks during infrastructure or API downtime.
- Streak updates are atomic and accompanied by audit logging.

### 2.4. Scope & Permission Guard (`bot/utils/scope_guard.py` & `bot/cogs/scope.py`)
- Restricts commands to authorized channels using the `@require_scope("command_group")` decorator.
- Permitted groups: `dsa_track`, `leaderboard`, `config`, `all`.
- Ensures administrative commands run only in private `#dsa-config` channels.

---

## 3. Developer Best Practices

1. **Keep Commands Scoped**: When adding a new slash command, apply `@require_scope("<group>")` to preserve server isolation.
2. **Ephemeral Responses for Errors**: Use `ephemeral=True` for error notifications, permission rejections, and redirect notices to keep public channels clean.
3. **Audit Logging**: Any administrative or state-altering command (e.g. manual verification, role scope updates, streak resets) must write an entry to the `audit_log` table.
4. **Preserve Privacy**: Never broadcast member user IDs as mentions `<@user_id>` in bulk embeds (such as the Wordle-style solver card). Use display names only.

---

## 4. Submitting Changes

1. Verify all modules compile cleanly:
   ```bash
   python3 -m py_compile bot/**/*.py
   ```
2. Test commands locally with `DEV_MODE=true`.
3. Ensure documentation in `docs/` is updated in the same pull request.
4. Open a pull request with a descriptive summary of changes and validation steps.
