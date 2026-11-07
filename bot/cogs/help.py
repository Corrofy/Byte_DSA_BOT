import discord
from discord import app_commands
from discord.ext import commands
from bot.utils.scope_guard import require_scope

BYTE_AVATAR = "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=120&h=120&fit=crop"

class HelpCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="help", description="Learn how DSA_DAILY works and view all available commands")
    @app_commands.describe(category="Filter commands by category")
    @app_commands.choices(category=[
        app_commands.Choice(name="All Commands", value="all"),
        app_commands.Choice(name="User & Verification", value="user"),
        app_commands.Choice(name="Streaks & Leaderboard", value="stats"),
        app_commands.Choice(name="Server Admin & Setup", value="admin"),
        app_commands.Choice(name="Bot Persona & Philosophy", value="persona"),
    ])
    @require_scope("dsa_track")
    async def help_cmd(self, interaction: discord.Interaction, category: str = "all"):
        if category == "persona":
            embed = discord.Embed(
                title="🤖 Meet Byte — Your Algorithm Sensei",
                description=(
                    "**“A daily O(1) commitment beats an all-nighter before an interview.”**\n\n"
                    "**Name:** Byte (DSA_DAILY Bot)\n"
                    "**Archetype:** Algorithmic Sparring Partner & Consistency Coach\n"
                    "**Personality:** Encouraging, witty, disciplined, geeky, and humble.\n\n"
                    "**Backstory:**\n"
                    "Born in an old memory register of a competitive programming server, Byte watched brilliant developers burn out after cramming 200 LeetCode problems in a week—only to forget them by interview day.\n\n"
                    "Byte was compiled to build a sustainable daily habit: one shared challenge per track every UTC day, unbroken streaks, and zero-spoiler discussions. Byte loves clean code, monotonic stacks, and watching you build unstoppable momentum!"
                ),
                color=0x5865F2,
            )
            embed.set_thumbnail(url=BYTE_AVATAR)
            embed.set_footer(text="DSA_DAILY • Consistency is your best runtime optimization")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        embed = discord.Embed(
            title="📖 DSA_DAILY — Bot Command & Usage Guide",
            description=(
                "Welcome to **DSA_DAILY**! We turn DSA practice into a daily habit like Wordle.\n"
                "• **3 Global Tracks:** Easy (1 pt), Medium (2 pts), Hard (3 pts)\n"
                "• **Daily Reset:** 00:00 UTC\n"
                "• **Verification:** Fresh accepted LeetCode solves"
            ),
            color=0x5865F2,
        )
        embed.set_thumbnail(url=BYTE_AVATAR)

        if category in ["all", "user"]:
            embed.add_field(
                name="👤 Getting Started & Linking",
                value=(
                    "• `/link username:<name>` — Link your LeetCode handle via bio code\n"
                    "• `/link action:verify` — Verify ownership after updating your bio\n"
                    "• `/unlink` — Disconnect your LeetCode username\n"
                    "• `/verify [track]` — Verify your solve for today's challenge\n"
                    "• `/subscribe track:<easy|med|hard>` — Opt-in to daily notification ping\n"
                    "• `/unsubscribe track:<track>` — Remove notification role"
                ),
                inline=False,
            )

        if category in ["all", "stats"]:
            embed.add_field(
                name="🔥 Streaks, Stats & Leaderboards",
                value=(
                    "• `/profile [user]` — Detailed stats, track streaks & languages used\n"
                    "• `/streak` — Quick glance at your current active streak\n"
                    "• `/leaderboard track:<track> scope:<server|global>` — View rankings\n"
                    "• `/share` — Copy your Wordle-style spoiler-free daily card\n"
                    "• `/privacy leaderboard:<on|off> leetcode:<on|off>` — Privacy settings"
                ),
                inline=False,
            )

        if category in ["all", "admin"]:
            embed.add_field(
                name="⚙️ Server Admin & Setup",
                value=(
                    "• `/setup track:<track> channel:#chan` — Bind a channel to a track\n"
                    "• `/settings threads:<on|off> recap-channel:#chan` — Toggle threads & recap\n"
                    "• `/setmessage track:<track> text:<msg> role:@role` — Custom daily ping\n"
                    "• `/setmessage-all text:<msg>` — Shortcut for all tracks\n"
                    "• `/setmessage-recap text:<msg>` — Custom weekly recap message\n"
                    "• `/admin_health` — Bot diagnostics, latency, and DB status\n"
                    "• `/admin_grace date:<YYYY-MM-DD>` — Outage streak preservation (Owner)"
                ),
                inline=False,
            )

        embed.set_footer(text="Run /usage for a quick 4-step onboarding guide • Powered by Byte")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="usage", description="Step-by-step onboarding walkthrough for beginners")
    @require_scope("dsa_track")
    async def usage_cmd(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🚀 How to Use DSA_DAILY in 4 Simple Steps",
            description="Follow this quick routine to build an unbroken coding streak:",
            color=0x57F287,
        )
        embed.set_thumbnail(url=BYTE_AVATAR)

        embed.add_field(
            name="1️⃣ Link Your Account (One-Time)",
            value="Run `/link username:<your_leetcode_handle>`. Paste the verification code in your LeetCode **About Me** bio, then run `/link action:verify`.",
            inline=False,
        )
        embed.add_field(
            name="2️⃣ Pick Your Track & Subscribe",
            value="Self-assign notification roles with `/subscribe track:easy` (or `medium`/`hard`). You will get pinged when challenges drop at **00:00 UTC**.",
            inline=False,
        )
        embed.add_field(
            name="3️⃣ Solve on LeetCode",
            value="Click the problem link in the daily embed. Solve and submit on LeetCode. Ensure your submission history is set to **Public** in LeetCode Privacy settings.",
            inline=False,
        )
        embed.add_field(
            name="4️⃣ Verify & Share Your Card",
            value="Click the **[Verify my solve]** button on the daily Discord embed. Then click **[Share result]** to copy your daily Wordle-style card into chat!",
            inline=False,
        )

        embed.set_footer(text="Need more commands? Run /help • Built by Byte")
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(HelpCog(bot))
