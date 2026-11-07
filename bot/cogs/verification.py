from datetime import datetime, timezone, date
import discord
from discord import app_commands
from discord.ext import commands, tasks
from sqlalchemy import select
from bot.db.session import async_session
from bot.db.models import User, DailyChallenge, Track, Solve, Streak
from bot.services.verification import verification_service
from bot.utils.scope_guard import require_scope


class VerificationCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.reconciliation_loop.start()

    def cog_unload(self):
        self.reconciliation_loop.cancel()

    @tasks.loop(minutes=1)
    async def reconciliation_loop(self):
        now_utc = datetime.now(timezone.utc)
        # Nightly reconciliation at 23:30 UTC
        if now_utc.hour == 23 and now_utc.minute == 30:
            await self.reconcile_active_streaks()

    @reconciliation_loop.before_loop
    async def before_reconcile(self):
        await self.bot.wait_until_ready()

    async def reconcile_active_streaks(self):
        today_utc = date.today()
        async with async_session() as session:
            # Users with active streaks who haven't solved today
            active_users = (
                await session.execute(
                    select(User)
                    .join(Streak, Streak.user_id == User.id)
                    .where(Streak.current > 0, User.link_status == "verified")
                    .distinct()
                )
            ).scalars().all()

            challenges = (
                await session.execute(
                    select(DailyChallenge).where(DailyChallenge.challenge_date == today_utc)
                )
            ).scalars().all()

            for user in active_users:
                for ch in challenges:
                    try:
                        await verification_service.verify_challenge_solve(user.id, ch.id, session)
                    except Exception:
                        pass

    @app_commands.command(name="verify", description="Verify your solve for today's challenge")
    @app_commands.describe(track="Select difficulty track (easy, medium, hard)")
    @require_scope("dsa_track")
    async def verify_cmd(self, interaction: discord.Interaction, track: str):
        await interaction.response.defer(ephemeral=True)
        track_slug = track.lower().strip()

        async with async_session() as session:
            user = (
                await session.execute(select(User).where(User.discord_id == interaction.user.id))
            ).scalar_one_or_none()

            if not user or user.link_status != "verified":
                await interaction.followup.send(
                    "⚠️ Please link your LeetCode account first using `/link username:<name>`", ephemeral=True
                )
                return

            t = (await session.execute(select(Track).where(Track.slug == track_slug))).scalar_one_or_none()
            if not t:
                await interaction.followup.send("❌ Invalid track. Choose `easy`, `medium`, or `hard`.", ephemeral=True)
                return

            today_utc = date.today()
            ch = (
                await session.execute(
                    select(DailyChallenge).where(
                        DailyChallenge.challenge_date == today_utc, DailyChallenge.track_id == t.id
                    )
                )
            ).scalar_one_or_none()

            if not ch:
                await interaction.followup.send(f"❌ No active challenge for {track_slug} today.", ephemeral=True)
                return

            res = await verification_service.verify_challenge_solve(user.id, ch.id, session)
            await interaction.followup.send(res.message, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(VerificationCog(bot))
