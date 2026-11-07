# DSA_DAILY — User Onboarding & Usage Guide

This guide walks members and administrators through using **DSA_DAILY** (Byte) from onboarding to daily habit tracking.

---

## 1. Quick Member Routine (The 4-Step Habit)

### Step 1: Connect LeetCode Account (One-Time)
1. Run:
   ```text
   /link username:<your_leetcode_handle>
   ```
2. Byte generates a verification code (e.g. `DSA_DAILY-8F2B1C`).
3. Paste this code into your public LeetCode profile **About Me** bio field.
4. Run:
   ```text
   /link action:verify
   ```

### Step 2: Opt-In to Notifications
Self-assign difficulty track notification roles:
```text
/subscribe track:easy
/subscribe track:medium
/subscribe track:hard
```
*(Use `/unsubscribe track:<track>` anytime to remove a notification role).*

### Step 3: Solve Daily Problems
- Challenges release daily at **00:00 UTC** in dedicated track channels (e.g. `#dsa-easy`, `#dsa-medium`, `#dsa-hard`).
- Open the problem URL and submit an accepted solution on LeetCode.
- *Note:* Ensure submission history is set to **Public** in LeetCode Privacy settings.

### Step 4: Verify & Share Results
1. In the daily challenge embed, click the **[✅ Verify my solve]** button (or run `/verify track:<track>`).
2. Once verified, click **[📋 Share result]** or run `/share` to copy your spoiler-free Wordle-style card into chat:
   ```text
   DSA_DAILY #42
   Easy   ✅
   Medium ✅
   Hard   ⬜
   2/3 solved · Streak 7 🔥
   ```

---

## 2. Streak & Stats Commands
- `/streak`: Quick view of your current active streak and personal record.
- `/profile [user]`: Comprehensive card with easy/medium/hard breakdown, longest streaks, and languages used.
- `/leaderboard [track:easy|medium|hard|overall] [scope:server|global]`: Community standings and the Server Collective Streak banner.
- `/privacy [leaderboard:true|false] [leetcode:true|false]`: Opt in or out of public leaderboards or mask your LeetCode handle.

---

## 3. Administrator Setup & Scope Management

### A. Bot Scope & Channel Isolation
Admins can bind Byte to a specific role and restrict commands to dedicated channels:

1. **Assign Bot Scope Role**:
   ```text
   /scope set-role role:@dsaBot
   ```
2. **Designate Private Config Channel** (`#dsa-config`):
   ```text
   /scope channel set-config channel:#dsa-config
   ```
   *Keeps configuration (`/setup`, `/settings`, `/scope`, `/admin_*`) restricted to admins and moderators.*
3. **Designate Leaderboard Channel** (`#dsa-leaderboard`):
   ```text
   /scope channel set-leaderboard channel:#dsa-leaderboard
   ```
4. **Permit Solver Commands in Track Channels**:
   ```text
   /scope channel add channel:#dsa-easy commands:dsa_track
   /scope channel add channel:#dsa-medium commands:dsa_track
   /scope channel add channel:#dsa-hard commands:dsa_track
   ```
5. **View Active Configuration**:
   ```text
   /scope view
   ```

### B. Channel Track Binding & Announcements
Inside `#dsa-config`:
```text
/setup track:easy channel:#dsa-easy
/setup track:medium channel:#dsa-medium
/setup track:hard channel:#dsa-hard
/settings threads:on recap-channel:#dsa-leaderboard show_solvers:on
```

---

## 4. Help & Support
- `/help`: Complete categorized command manual and Byte's persona lore.
- `/usage`: In-Discord walkthrough identical to the 4-step routine above.
