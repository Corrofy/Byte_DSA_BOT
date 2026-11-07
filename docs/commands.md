# DSA_DAILY — Complete Command Reference

This document provides a comprehensive, structured reference for all Discord application slash commands supported by **DSA_DAILY**.

---

## 1. User & Solver Commands

These commands are available to every server member.

### `/help`
- **Description**: Displays the interactive command guide, category filters, and Byte's persona lore.
- **Options**:
  - `category` *(optional, string)*: Filter by `all`, `user`, `stats`, `admin`, or `persona`.
- **Permission**: Anyone
- **Example**: `/help category:user`

### `/usage`
- **Description**: Displays the step-by-step 4-stage routine (linking, subscribing, solving, verifying, sharing).
- **Options**: None
- **Permission**: Anyone
- **Example**: `/usage`

### `/link`
- **Description**: Connects your Discord account to your public LeetCode username via bio code proof.
- **Options**:
  - `username` *(optional, string)*: Your LeetCode handle (e.g. `alex_dev`).
  - `action` *(optional, string)*: Set to `verify` after pasting the code in your bio.
- **Permission**: Anyone
- **Process**:
  1. `/link username:your_handle` ➔ generates `DSA_DAILY-A1B2C3` (10-minute expiry).
  2. User puts code in LeetCode profile **About Me** field.
  3. `/link action:verify` ➔ verifies ownership and consumes token.

### `/unlink`
- **Description**: Disconnects your linked LeetCode username from your Discord user ID.
- **Options**: None
- **Permission**: Anyone
- **Example**: `/unlink`

### `/verify`
- **Description**: Checks LeetCode's public GraphQL API for your accepted submission today.
- **Options**:
  - `track` *(required, string)*: Difficulty track (`easy`, `medium`, or `hard`).
- **Permission**: Anyone
- **Rule**: Must be solved during the current UTC challenge date window `[00:00, 24:00)`.

### `/subscribe`
- **Description**: Self-assigns the notification role for a difficulty track to receive daily pings.
- **Options**:
  - `track` *(required, string)*: `easy`, `medium`, or `hard`.
- **Permission**: Anyone
- **Example**: `/subscribe track:medium`

### `/unsubscribe`
- **Description**: Removes the daily notification role for a difficulty track.
- **Options**:
  - `track` *(required, string)*: `easy`, `medium`, or `hard`.
- **Permission**: Anyone
- **Example**: `/unsubscribe track:easy`

---

## 2. Stats, Streaks & Leaderboard Commands

### `/profile`
- **Description**: Displays comprehensive solver card including track streaks, overall streak, total solves, and languages used.
- **Options**:
  - `user` *(optional, user)*: Another member to inspect (defaults to yourself).
- **Permission**: Anyone
- **Example**: `/profile user:@Devin`

### `/streak`
- **Description**: Quick response showing your active daily streak and personal record.
- **Options**: None
- **Permission**: Anyone
- **Example**: `/streak`

### `/leaderboard`
- **Description**: Displays the server or global rankings and points tally, along with the **Server Collective Streak**.
- **Options**:
  - `track` *(optional, string)*: `overall` (points-based), `easy`, `medium`, or `hard` (streak-based). Defaults to `overall`.
  - `scope` *(optional, string)*: `server` (members of current guild) or `global` (all users). Defaults to `server`.
- **Scoring**:
  - Easy: 1 pt
  - Medium: 2 pts
  - Hard: 3 pts
- **Tie-breakers**:
  - Overall: Points ➔ Total Solves ➔ Current Streak
  - Track: Current Streak ➔ Longest Streak ➔ Total Solves
- **Server Collective Streak Banner**: Shows the collective streak of the entire Discord community!

### `/share`
- **Description**: Generates the copyable Wordle-style spoiler-free daily card.
- **Options**: None
- **Permission**: Anyone
- **Output format**:
  ```text
  DSA_DAILY #42
  Easy   ✅
  Medium ✅
  Hard   ⬜
  2/3 solved · Streak 7 🔥
  ```

### `/privacy`
- **Description**: Controls your appearance on public leaderboards and username visibility.
- **Options**:
  - `leaderboard` *(optional, boolean)*: `true` to show on boards, `false` to opt-out.
  - `leetcode` *(optional, boolean)*: `true` to display LeetCode handle publicly, `false` to mask as `(Hidden)`.
- **Permission**: Anyone
- **Example**: `/privacy leaderboard:true leetcode:false`

---

## 3. Server Admin & Moderator Commands

These commands require `Manage Server` or `Manage Messages` permissions.

### `/setup`
- **Description**: Binds a Discord channel to an Easy, Medium, or Hard difficulty track.
- **Options**:
  - `track` *(required, string)*: `easy`, `medium`, or `hard`.
  - `channel` *(required, channel)*: Target text channel (e.g. `#dsa-easy`).
- **Permission**: `Manage Server`
- **Rule**: One track per channel; one channel per track per guild. Duplicate bindings are rejected.

### `/settings`
- **Description**: Configures server-wide thread discussions, weekly recap channel, and Wordle-style solver presence cards.
- **Options**:
  - `threads` *(optional, boolean)*: `true` to create spoiler discussion threads under daily posts.
  - `recap_channel` *(optional, channel)*: Channel where Sunday 18:00 UTC recaps post.
  - `show_solvers` *(optional, boolean)*: `true` to display the Wordle-style "👥 Solvers Today" card listing who solved today with their streaks (display names only, **no @mentions**), or `false` to keep posts minimal.
- **Permission**: `Manage Server`
- **Example**: `/settings show_solvers:true` or `/settings show_solvers:false`

### `/setmessage`
- **Description**: Configures custom announcement text and opt-in notification role for a track.
- **Options**:
  - `track` *(required, string)*: `easy`, `medium`, or `hard`.
  - `text` *(optional, string)*: Custom message text (e.g. `"Good morning team! Easy challenge released:"`).
  - `role` *(optional, role)*: Opt-in ping role (e.g. `@DSA-Easy`). `@everyone` and `@here` are blocked.
- **Permission**: `Manage Messages` (for text), `Manage Server` (for role).

### `/setmessage-all`
- **Description**: Convenience command to set the same announcement text for all daily tracks.
- **Options**:
  - `text` *(required, string)*: Announcement text.
- **Permission**: `Manage Messages`

### `/setmessage-recap`
- **Description**: Configures custom text for the Sunday 18:00 UTC leaderboard recap post.
- **Options**:
  - `text` *(required, string)*: Recap intro text.
- **Permission**: `Manage Messages`

### `/scope set-role`
- **Description**: Assigns a bounding Discord role to Byte (the bot) to record and gate its overall server permissions.
- **Options**:
  - `role` *(required, role)*: Target role (e.g. `@dsaBot`).
- **Permission**: `Manage Server`

### `/scope view`
- **Description**: Displays the active bot scope summary, designated config and leaderboard channels, and channel command mappings.
- **Permission**: `Manage Server`

### `/scope channel add`
- **Description**: Grants permission for a command group to be executed within a specific channel.
- **Options**:
  - `channel` *(required, channel)*: Target channel (e.g. `#dsa-easy`).
  - `commands` *(required, choice)*: Command group (`dsa_track`, `leaderboard`, `config`, or `all`).
- **Permission**: `Manage Server`

### `/scope channel remove`
- **Description**: Revokes a command group from a channel.
- **Options**:
  - `channel` *(required, channel)*: Target channel.
  - `commands` *(required, choice)*: Command group to remove.
- **Permission**: `Manage Server`

### `/scope channel set-config`
- **Description**: Designates a private channel exclusively for bot configuration and administrative commands (`/setup`, `/settings`, `/admin_*`, `/scope`).
- **Options**:
  - `channel` *(required, channel)*: Private channel (e.g. `#dsa-config`).
- **Permission**: `Manage Server`

### `/scope channel set-leaderboard`
- **Description**: Designates a channel exclusively for leaderboard commands (`/leaderboard`).
- **Options**:
  - `channel` *(required, channel)*: Target channel (e.g. `#dsa-leaderboard`).
- **Permission**: `Manage Server`

---

## 4. Bot Owner & Emergency Diagnostics

Restricted to `OWNER_DISCORD_ID`.

### `/admin_health`
- **Description**: Live system diagnostics including gateway latency, SQLite WAL database connection, scheduled challenges, and total verified solves.
- **Permission**: Bot Owner / Delegated Moderators

### `/admin_grace`
- **Description**: Registers an **Outage Grace Day** for a specific UTC calendar date.
- **Options**:
  - `date` *(required, string)*: `YYYY-MM-DD`.
  - `reason` *(optional, string)*: Reason for outage (e.g. `"LeetCode API 500 error"`).
- **Rule**: Preserves streak continuity across all users without generating fake solves or points.

### `/admin_verify`
- **Description**: Manually credits a solve to a user if LeetCode API is unreachable or rate-limited.
- **Options**:
  - `user` *(required, user)*: Target Discord user.
  - `track` *(required, string)*: `easy`, `medium`, or `hard`.
  - `challenge_date` *(required, string)*: `YYYY-MM-DD`.
- **Permission**: Bot Owner / Delegated Moderators (Audit-logged).

---

## 5. Developer & Testing Commands (`DEV_MODE = true`)

Enabled only when `DEV_MODE=true` is set in the environment or `.env`. Designed for fast local testing and debugging without waiting for scheduled UTC cron loops. See [DevGuide.md](./DevGuide.md) for complete instructions.

### `/test problem now`
- **Description**: Immediately generates/fetches and dispatches the daily challenge embed for a difficulty track to the current channel. Bypasses the 00:00 UTC schedule and idempotency barriers.
- **Options**:
  - `action` *(optional, string)*: `now` (default, dispatches to channel) or `preview` (ephemeral only to you).
  - `track` *(optional, string)*: `easy` (default), `medium`, or `hard`.
- **Permission**: Developer / Server Admin
- **Example**: `/test problem action:now track:easy`

### `/test status`
- **Description**: Displays real-time dev environment status, UTC clock, active SQLite WAL database file, and registered entity counts.
- **Permission**: Developer (ephemeral)
- **Example**: `/test status`

### `/test solve`
- **Description**: Instantly simulates an accepted LeetCode solve for a user and track, testing streak increments and points calculation.
- **Options**:
  - `track` *(optional, string)*: `easy` (default), `medium`, or `hard`.
  - `user` *(optional, user)*: Member to credit (defaults to yourself).
  - `language` *(optional, string)*: Programming language (defaults to `Python3`).
- **Permission**: Developer
- **Example**: `/test solve track:medium language:Go`

### `/test reset_streak`
- **Description**: Resets all streak counters for a user to test broken streak mechanics and recovery.
- **Options**:
  - `user` *(optional, user)*: Member whose streak to clear.
- **Permission**: Developer
- **Example**: `/test reset_streak`
