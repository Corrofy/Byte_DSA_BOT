from datetime import date, datetime, timezone
import discord
from discord import app_commands
from discord.ext import commands
from sqlalchemy import select, delete
from bot.config import settings
from bot.db.session import async_session
from bot.db.models import (
    Track,
    DailyChallenge,
    Solve,
    Streak,
    OverallStreak,
    GuildSettings,
    GuildTrackSettings,
    User,
    AuditLog,
)
from bot.services.problems import problem_service
from bot.services.streaks import compute_user_streaks
from bot.ui.embeds import create_daily_embed
from bot.ui.buttons import DailyChallengeView


class DevCog(commands.Cog):
    """Developer testing cog enabled when DEV_MODE = True in .env"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    test_group = app_commands.Group(
        name="test",
        description="Developer mode commands for rapid testing & validation (DEV_MODE=true)",
    )

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if not settings.DEV_MODE:
            await interaction.response.send_message(
                "❌ **Developer mode is disabled.**\n"
                "To use `/test` commands, set `DEV_MODE=true` in your `bot/.env` file and restart the bot.\n"
                "See `docs/DevGuide.md` for full instructions.",
                ephemeral=True,
            )
            return False
        return True

    @test_group.command(
        name="status",
        description="Display active developer mode status, environment flags, and database statistics",
    )
    async def dev_status(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        async with async_session() as session:
            tracks = (await session.execute(select(Track))).scalars().all()
            challenges = (await session.execute(select(DailyChallenge))).scalars().all()
            solves = (await session.execute(select(Solve))).scalars().all()
            users = (await session.execute(select(User))).scalars().all()

        now_utc = datetime.now(timezone.utc)
        embed = discord.Embed(
            title="🧪 DSA_DAILY Developer Mode — Status & Diagnostics",
            color=0x5865F2,
            description="Developer commands are active! Use this environment for instant end-to-end verification.",
        )
        embed.add_field(name="DEV_MODE Flag", value=f"`{settings.DEV_MODE}`", inline=True)
        embed.add_field(name="Current UTC Time", value=f"`{now_utc.strftime('%Y-%m-%d %H:%M:%S UTC')}`", inline=True)
        embed.add_field(name="Gateway Latency", value=f"`{round(self.bot.latency * 1000, 1)}ms`", inline=True)
        embed.add_field(name="Database File", value=f"`{settings.DATABASE_URL}`", inline=False)
        embed.add_field(name="Active Tracks", value=f"`{len(tracks)}` ({', '.join(t.slug for t in tracks)})", inline=True)
        embed.add_field(name="Challenges In DB", value=f"`{len(challenges)}`", inline=True)
        embed.add_field(name="Total Users / Solves", value=f"`{len(users)}` users / `{len(solves)}` solves", inline=True)

        if settings.DEV_GUILD_ID:
            embed.add_field(name="Fast Sync Guild ID", value=f"`{settings.DEV_GUILD_ID}`", inline=False)

        embed.set_footer(text="See docs/DevGuide.md for developer workflows and command cheat-sheet.")
        await interaction.followup.send(embed=embed, ephemeral=True)

    @test_group.command(
        name="problem",
        description="Force-generate and immediately dispatch daily challenge to current channel (no wait)",
    )
    @app_commands.describe(
        action="Action to execute (use 'now' to dispatch immediately)",
        track="Difficulty track to dispatch (defaults to easy)",
    )
    @app_commands.choices(
        action=[
            app_commands.Choice(name="now — Dispatch immediately to this channel", value="now"),
            app_commands.Choice(name="preview — Ephemeral preview only", value="preview"),
        ],
        track=[
            app_commands.Choice(name="Easy", value="easy"),
            app_commands.Choice(name="Medium", value="medium"),
            app_commands.Choice(name="Hard", value="hard"),
        ],
    )
    async def test_problem(
        self,
        interaction: discord.Interaction,
        action: str = "now",
        track: str = "easy",
    ):
        await interaction.response.defer(ephemeral=(action == "preview"))
        today_utc = date.today()

        async with async_session() as session:
            # 1. Fetch or create today's challenge for the selected track
            ch = await problem_service.get_or_create_daily_challenge(track, today_utc, session)
            if not ch:
                await interaction.followup.send(f"❌ Failed to find or generate a challenge for track `{track}`.")
                return

            # Count solvers today for embed
            solves_today = (
                await session.execute(select(Solve).where(Solve.challenge_id == ch.id))
            ).scalars().all()
            solver_names = []
            for s in solves_today:
                u = (await session.execute(select(User).where(User.id == s.user_id))).scalar_one_or_none()
                if u:
                    solver_names.append(u.display_name or f"User {u.id}")

            embed = create_daily_embed(
                challenge=ch,
                solved_count=len(solves_today),
                solvers=solver_names,
                show_solvers=True,
            )
            embed.set_author(name="🧪 [DEV_MODE TEST DISPATCH]", icon_url="https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=100&h=100&fit=crop")

            view = DailyChallengeView(challenge_id=ch.id)

            if action == "preview":
                await interaction.followup.send(
                    content=f"🧪 **[DEV PREVIEW]** Daily challenge for **{track.capitalize()}** track on `{today_utc}`:",
                    embed=embed,
                    view=view,
                    ephemeral=True,
                )
                return

            # Dispatch live to current channel
            channel = interaction.channel
            sent_msg = await channel.send(
                content=f"🧪 **[DEV_MODE TEST DISPATCH]** Triggered via `/test problem now` by {interaction.user.mention}:",
                embed=embed,
                view=view,
            )

            # Audit log
            log = AuditLog(
                guild_id=interaction.guild_id,
                actor_discord_id=interaction.user.id,
                action="DEV_TEST_PROBLEM_DISPATCH",
                target_type="CHANNEL",
                target_id=str(interaction.channel_id),
                details_json=f'{{"track": "{track}", "challenge_id": {ch.id}, "message_id": {sent_msg.id}}}',
            )
            session.add(log)
            await session.commit()

            # Attempt optional thread creation
            if interaction.guild_id:
                gs = (
                    await session.execute(
                        select(GuildSettings).where(GuildSettings.guild_id == interaction.guild_id)
                    )
                ).scalar_one_or_none()
                if gs and gs.threads_enabled:
                    try:
                        thread = await sent_msg.create_thread(
                            name=f"[TEST] DSA #{ch.challenge_number} — {track.capitalize()}",
                            auto_archive_duration=1440,
                        )
                        await thread.send(
                            "💡 Discussion space for test challenge! Remember to use `||spoiler tags||` for solution codes."
                        )
                    except Exception:
                        pass

            await interaction.followup.send(
                f"✅ **Dispatched test challenge for `{track}` into {channel.mention}!**\n"
                f"Message ID: `{sent_msg.id}` • Challenge #{ch.challenge_number}: **{ch.problem.title}**",
                ephemeral=True,
            )

    @test_group.command(
        name="solve",
        description="Instantly simulate an accepted solve for a user and track (no LeetCode wait)",
    )
    @app_commands.describe(
        track="Track difficulty (easy, medium, hard)",
        user="Target user to credit solve to (defaults to yourself)",
        language="Programming language used (defaults to Python3)",
    )
    @app_commands.choices(
        track=[
            app_commands.Choice(name="Easy", value="easy"),
            app_commands.Choice(name="Medium", value="medium"),
            app_commands.Choice(name="Hard", value="hard"),
        ]
    )
    async def test_solve(
        self,
        interaction: discord.Interaction,
        track: str = "easy",
        user: discord.Member | None = None,
        language: str = "Python3",
    ):
        await interaction.response.defer(ephemeral=True)
        target_user = user or interaction.user
        today_utc = date.today()

        async with async_session() as session:
            # Look up or auto-create internal user for testing
            db_user = (
                await session.execute(select(User).where(User.discord_id == target_user.id))
            ).scalar_one_or_none()

            if not db_user:
                db_user = User(
                    discord_id=target_user.id,
                    display_name=target_user.display_name,
                    leetcode_username=f"dev_{target_user.name.lower()}",
                    link_status="verified",
                )
                session.add(db_user)
                await session.flush()

            t = (await session.execute(select(Track).where(Track.slug == track.lower().strip()))).scalar_one_or_none()
            if not t:
                await interaction.followup.send("❌ Track not found.")
                return

            ch = await problem_service.get_or_create_daily_challenge(track, today_utc, session)

            # Record simulated solve
            solve = Solve(
                user_id=db_user.id,
                challenge_id=ch.id,
                track_id=t.id,
                leetcode_submission_id=f"sim_dev_{datetime.now().timestamp()}",
                solved_at=datetime.utcnow(),
                language=language,
                verification_method="dev_simulated",
                verified_at=datetime.utcnow(),
                verified_by=interaction.user.id,
            )
            session.add(solve)

            # Recompute streaks
            streaks = await compute_user_streaks(db_user.id, session)
            await session.commit()

            track_streak = streaks.get(track, 1)
            await interaction.followup.send(
                f"🎉 **[DEV SIMULATION]** Solve recorded for {target_user.mention} on **{track.capitalize()}** (#{ch.challenge_number} - *{ch.problem.title}*)!\n"
                f"• Solved with: `{language}`\n"
                f"• Current {track.capitalize()} Streak: `{track_streak}` 🔥\n"
                f"• Overall Points: `{streaks.get('points', 0)}` pts",
                ephemeral=True,
            )

    @test_group.command(
        name="reset_streak",
        description="Reset streak counters for a user (useful for testing broken streak behavior)",
    )
    @app_commands.describe(user="User whose streaks should be cleared (defaults to yourself)")
    async def test_reset_streak(
        self,
        interaction: discord.Interaction,
        user: discord.Member | None = None,
    ):
        await interaction.response.defer(ephemeral=True)
        target_user = user or interaction.user

        async with async_session() as session:
            db_user = (
                await session.execute(select(User).where(User.discord_id == target_user.id))
            ).scalar_one_or_none()

            if not db_user:
                await interaction.followup.send("❌ User not found in database.", ephemeral=True)
                return

            await session.execute(delete(Streak).where(Streak.user_id == db_user.id))
            await session.execute(delete(OverallStreak).where(OverallStreak.user_id == db_user.id))
            await session.commit()

        await interaction.followup.send(
            f"🔄 **[DEV MODE]** Reset all streak counters to 0 for {target_user.mention}. Ready to test new streak progression!",
            ephemeral=True,
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(DevCog(bot))
