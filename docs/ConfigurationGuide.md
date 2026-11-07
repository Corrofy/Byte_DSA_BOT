# DSA_DAILY — Complete Configuration & Customization Guide

This guide walks administrators, community managers, and developers through customizing every aspect of **DSA_DAILY**, from daily announcement messages and role pings to Byte's persona dialogue, storytelling text, and server-level preferences.

---

## 1. Customizing Daily Track Messages & Mentions

By default, DSA_DAILY posts the problem embed silently without any text or pings. Server admins can customize announcements to fit the community's tone and culture.

### A. Setting Custom Per-Track Text
Run:
```text
/setmessage track:easy text:"🌅 Good morning engineers! Kickstart your brain with today's Easy problem:"
/setmessage track:medium text:"⚡ Core interview practice time! Today's Medium is live:"
/setmessage track:hard text:"🔥 Elite problem solvers: Today's Hard challenge has dropped!"
```

### B. Setting Up Opt-In Role Mentions
To notify interested members without pinging the entire server:
1. In your Discord server settings (Server Settings ➔ Roles), create three notification roles:
   - `@DSA-Easy`
   - `@DSA-Medium`
   - `@DSA-Hard`
   *(Ensure these roles are set to "Allow anyone to @mention this role" or that the bot sits above them in hierarchy).*
2. Bind the role to each track:
   ```text
   /setmessage track:easy role:@DSA-Easy
   /setmessage track:medium role:@DSA-Medium
   /setmessage track:hard role:@DSA-Hard
   ```
3. Members can now self-assign or remove their roles anytime using:
   - `/subscribe track:easy`
   - `/unsubscribe track:easy`

*Security Rule:* DSA_DAILY enforces strict Discord `allowed_mentions` that exclusively mention the specific configured track role. Global mentions (`@everyone`, `@here`) are automatically rejected.

---

## 2. Configuring Weekly Sunday Recaps

Every Sunday at 18:00 UTC, DSA_DAILY can post a celebratory weekly recap highlighting the server's top solvers and the community's collective streak.

1. Designate a recap channel (e.g. `#dsa-leaderboard` or `#announcements`):
   ```text
   /settings recap-channel:#dsa-leaderboard
   ```
2. Customize the recap announcement message:
   ```text
   /setmessage-recap text:"🏆 **DSA_DAILY Weekly Champion Recap is here!** Congratulations to our top streak holders!"
   ```
*Note:* Weekly recap posts **never ping roles** to avoid Sunday evening noise.

---

## 3. Configuring Discussion Threads

To keep challenge channels clean and spoiler-free:
1. Enable automatic thread creation:
   ```text
   /settings threads:on
   ```
2. When a challenge posts at 00:00 UTC, the bot automatically spawns a dedicated public thread:
   - Name: `DSA #42 — Easy Discussion`
   - Auto-archives after 24 hours.
   - Posts a reminder: *"💡 Discussion space for today's challenge! Remember to use `||spoiler tags||` for solution codes."*

---

## 4. Customizing Byte's Persona, Lore & Voice Lines

Byte's personality is defined in `bot/cogs/help.py` and `bot/ui/embeds.py`. You can adjust Byte's quotes, tone, or backstory to match your community:

### Changing Byte's Quotes & Personality in Code
Open `bot/cogs/help.py` and modify the `persona` embed text:
```python
# In bot/cogs/help.py:
embed = discord.Embed(
    title="🤖 Meet Byte — Your Algorithm Sensei",
    description=(
        "**“A daily O(1) commitment beats an all-nighter before an interview.”**\n\n"
        "**Name:** Byte (DSA_DAILY Bot)\n"
        "**Archetype:** Algorithmic Sparring Partner & Consistency Coach\n"
        "..."
    ),
    color=0x5865F2,
)
```

### Changing Colors & Difficulty Badges
In `bot/ui/embeds.py`, you can customize the Discord embed accent colors:
```python
COLOR_MAP = {
    "EASY": 0x57F287,    # Discord Green
    "MEDIUM": 0xFEE75C,  # Discord Yellow / Gold
    "HARD": 0xED4245,    # Discord Coral / Red
}
```

---

## 5. Outage Grace Days & Streak Protection

If LeetCode suffers an outage (e.g. HTTP 500 or 429 rate limit) or the host machine loses network connectivity:
1. As the Bot Owner, run:
   ```text
   /admin_grace date:YYYY-MM-DD reason:"LeetCode API 429 rate limit downtime"
   ```
2. This creates an `OutageGraceDay` row in the SQLite database.
3. Streak calculation engines will treat that calendar date as solved for all users, preserving consecutive streak continuity without awarding fake solve counts or points!

---

## 6. Server Collective Streak Tracking

In addition to individual solver streaks, DSA_DAILY tracks the **Server Collective Streak** (inspired by Wordle's group stats).
- **Rule**: If at least one server member logs a verified solve on a UTC challenge day, the server's collective streak increments by +1.
- Displayed prominently on the `/leaderboard` command and within the web studio dashboard:
  - **Current Server Streak** (e.g. `14 Days Unbroken 🔥`)
  - **Longest Server Streak** (e.g. `28 Days Record`)
  - **Daily Community Consistency Rate** (e.g. `87%`)

---

## 7. Wordle-Style Solver Presence ("Who Was Playing")

### What is it?
When Wordle reveals that your friends played today, it creates a powerful social nudge that sparks urgency and friendly competition. DSA_DAILY brings this exact mechanic to Discord.

Whenever a member solves the day's problem, the daily challenge post updates with a Wordle-style card:
```text
👥 Solvers Today (Wordle-Style)
_Sarah Chen 🔥5, Devin Neo 🔥3, Priya Sharma 🔥2_ solved today!
[✅ Verify my solve]  [📋 Share result]
```

### Critical Privacy Rule: No Notification Pings
To keep member channels pleasant and avoid spamming server members:
- Solvers are formatted using **plain text display names and streak badges only**.
- Bot embeds **NEVER** use `<@user_id>` in this card, ensuring no one gets annoying notification sounds or unread red badge counts.

### How to Enable or Disable per Server
Because some servers prefer ultra-minimal posts while others crave maximum engagement, this is 100% configurable per guild:
1. **Via Slash Command**:
   - Turn ON: `/settings show_solvers:true` (or `/settings show_solvers:on`)
   - Turn OFF: `/settings show_solvers:false` (or `/settings show_solvers:off`)
2. **Via Web Studio Settings**:
   - Click the ⚙️ icon next to the server name in the Discord Simulator.
   - Toggle **Wordle-Style Solvers Card ("Who Was Playing")** on or off.
   - Click **Save Settings**.

---

## 8. Role-Based Bot Scoping & Channel Isolation

Server administrators can limit the bot to specific channels or categories and configure which slash commands are permitted in each channel.

### A. Assigning the Bot's Scope Role
1. In Discord **Server Settings ➔ Roles**, create a role for the bot (e.g. `@dsaBot`).
2. Assign permissions/channel overwrites to this role to control which channels and categories Byte can access.
3. Inform the bot of this role:
   ```text
   /scope set-role role:@dsaBot
   ```

### B. Designating Private Admin & Leaderboard Channels
To keep administrative operations clean and secure:
- **Designate Private Config Channel** (restricted to Admins/Moderators and Byte):
  ```text
  /scope channel set-config channel:#dsa-config
  ```
  Commands such as `/setup`, `/settings`, `/setmessage*`, `/admin_*`, and `/scope` will be restricted to this channel.
- **Designate Leaderboard Channel**:
  ```text
  /scope channel set-leaderboard channel:#dsa-leaderboard
  ```
  The `/leaderboard` command will be restricted to this channel.

### C. Mapping Slash Commands to Specific Channels
Admins can designate which command groups run in which channels:
```text
# Allow DSA track & solver commands in track channels:
/scope channel add channel:#dsa-easy commands:dsa_track
/scope channel add channel:#dsa-medium commands:dsa_track
/scope channel add channel:#dsa-hard commands:dsa_track

# Allow leaderboard commands in leaderboard channel:
/scope channel add channel:#dsa-leaderboard commands:leaderboard

# Allow config commands in config channel:
/scope channel add channel:#dsa-config commands:config
```

#### Command Groups Reference:
- `dsa_track`: `/verify`, `/link`, `/unlink`, `/subscribe`, `/unsubscribe`, `/share`, `/profile`, `/streak`, `/help`, `/usage`
- `leaderboard`: `/leaderboard`
- `config`: `/setup`, `/settings`, `/setmessage*`, `/admin_*`, `/scope`
- `all`: Unrestricted (all commands enabled)

### D. Inspecting Current Scope
View the entire server routing map at any time:
```text
/scope view
```
If a user runs a command in an unauthorized channel, Byte responds with an ephemeral message directing them to the permitted channel.
