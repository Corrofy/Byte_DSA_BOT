import discord
from discord import app_commands
from discord.ext import commands
from sqlalchemy import select
from bot.db.session import async_session
from bot.db.models import User, DailyChallenge, Solve, OverallStreak
from bot.services.leaderboards import leaderboard_service
from bot.ui.embeds import create_share_card_text
from bot.utils.scope_guard import require_scope


class LeaderboardCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="leaderboard", description="View track or overall points leaderboards")
    @app_commands.describe(
        track="Select track (easy, medium, hard, overall)",
        scope="View global or server leaderboard",
    )
    @require_scope("leaderboard")
    async def leaderboard(
        self,
        interaction: discord.Interaction,
        track: str = "overall",
        scope: str = "server",
    ):
        await interaction.response.defer()
        track_slug = track.lower().strip()
        is_server = scope.lower().strip() == "server"
        guild_id = interaction.guild_id if is_server else None

        async with async_session() as session:
            server_streak = await leaderboard_service.get_server_collective_streak(guild_id, session)
            streak_banner = (
                f"⚔️ **{'Server' if is_server else 'Global'} Collective Streak:** `{server_streak['current']}` Days Unbroken 🔥 "
                f"(Personal Best: `{server_streak['longest']}` Days • `{server_streak['total_active_days']}` Active Days)\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            )

            if track_slug == "overall":
                entries = await leaderboard_service.get_overall_leaderboard(guild_id, session, limit=10)
                title = f"🏆 Overall Leaderboard ({'Server' if is_server else 'Global'})"
                desc = streak_banner + "**Scoring:** Easy = 1 pt • Medium = 2 pts • Hard = 3 pts\n\n"
                if not entries:
                    desc += "*No solvers on the board yet.*"
                for e in entries:
                    medal = "🥇" if e.rank == 1 else "🥈" if e.rank == 2 else "🥉" if e.rank == 3 else f"`#{e.rank}`"
                    desc += f"{medal} {e.display_name} — **{e.points} pts** ({e.total_solves} solves • Streak: `{e.current_streak}` 🔥)\n"
            else:
                entries = await leaderboard_service.get_track_leaderboard(track_slug, guild_id, session, limit=10)
                title = f"⚡ {track_slug.capitalize()} Track Leaderboard ({'Server' if is_server else 'Global'})"
                desc = streak_banner + "**Ranked by:** Current Streak (Tiebreak: Longest Streak, Total Solves)\n\n"
                if not entries:
                    desc += "*No active streaks yet.*"
                for e in entries:
                    medal = "🥇" if e.rank == 1 else "🥈" if e.rank == 2 else "🥉" if e.rank == 3 else f"`#{e.rank}`"
                    desc += f"{medal} {e.display_name} — **Streak: `{e.current_streak}`** 🔥 (Longest: `{e.longest_streak}` • {e.total_solves} solves)\n"

            embed = discord.Embed(title=title, description=desc, color=0xFEE75C)
            await interaction.followup.send(embed=embed)

    @app_commands.command(name="share", description="Generate your daily Wordle-style DSA_DAILY share card")
    @require_scope("dsa_track")
    async def share(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        async with async_session() as session:
            user = (
                await session.execute(select(User).where(User.discord_id == interaction.user.id))
            ).scalar_one_or_none()

            if not user or user.link_status != "verified":
                await interaction.followup.send("⚠️ Link your LeetCode account with `/link` first.", ephemeral=True)
                return

            from datetime import date
            today_date = date.today()
            all_today_ch = (
                await session.execute(select(DailyChallenge).where(DailyChallenge.challenge_date == today_date))
            ).scalars().all()

            if not all_today_ch:
                await interaction.followup.send("No challenges active today yet.", ephemeral=True)
                return

            solves_today = (
                await session.execute(
                    select(Solve.track_id).where(
                        Solve.user_id == user.id,
                        Solve.challenge_id.in_([c.id for c in all_today_ch]),
                    )
                )
            ).scalars().all()

            easy_s = 1 in solves_today
            med_s = 2 in solves_today
            hard_s = 3 in solves_today

            ost = (
                await session.execute(select(OverallStreak).where(OverallStreak.user_id == user.id))
            ).scalar_one_or_none()

            streak_val = ost.current if ost else 0
            ch_num = all_today_ch[0].challenge_number

            card = create_share_card_text(ch_num, easy_s, med_s, hard_s, streak_val)
            await interaction.followup.send(
                f"📋 Copy and share your results in chat:\n```text\n{card}\n```", ephemeral=True
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(LeaderboardCog(bot))
