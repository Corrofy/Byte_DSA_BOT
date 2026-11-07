from datetime import date, datetime
import discord
from discord import app_commands
from discord.ext import commands
from sqlalchemy import select
from bot.config import settings
from bot.db.session import async_session
from bot.db.models import User, DailyChallenge, Track, Solve, OutageGraceDay, GuildTrackSettings, GuildSettings, AuditLog
from bot.services.streaks import compute_user_streaks
from bot.utils.scope_guard import require_scope


class AdminCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def is_owner(self, user_id: int) -> bool:
        return user_id == settings.OWNER_DISCORD_ID

    @app_commands.command(name="admin_verify", description="[Admin/Mod] Manually verify a user's solve")
    @app_commands.checks.has_permissions(manage_messages=True)
    @require_scope("config")
    async def admin_verify(
        self,
        interaction: discord.Interaction,
        user: discord.Member,
        track: str,
        challenge_date: str,
    ):
        await interaction.response.defer(ephemeral=True)
        try:
            target_date = datetime.strptime(challenge_date, "%Y-%m-%d").date()
        except ValueError:
            await interaction.followup.send("❌ Date format must be `YYYY-MM-DD`.", ephemeral=True)
            return

        async with async_session() as session:
            db_user = (
                await session.execute(select(User).where(User.discord_id == user.id))
            ).scalar_one_or_none()
            if not db_user:
                await interaction.followup.send("User has not interacted with the bot.", ephemeral=True)
                return

            t = (await session.execute(select(Track).where(Track.slug == track.lower().strip()))).scalar_one_or_none()
            if not t:
                await interaction.followup.send("Invalid track.", ephemeral=True)
                return

            ch = (
                await session.execute(
                    select(DailyChallenge).where(
                        DailyChallenge.challenge_date == target_date, DailyChallenge.track_id == t.id
                    )
                )
            ).scalar_one_or_none()
            if not ch:
                await interaction.followup.send("No challenge found for that date and track.", ephemeral=True)
                return

            # Record manual solve
            manual_solve = Solve(
                user_id=db_user.id,
                challenge_id=ch.id,
                track_id=t.id,
                leetcode_submission_id=f"manual_{interaction.id}",
                solved_at=datetime.combine(target_date, datetime.min.time()),
                language="manual",
                verification_method="manual",
                verified_at=datetime.utcnow(),
                verified_by=interaction.user.id,
            )
            session.add(manual_solve)

            # Audit log
            log = AuditLog(
                guild_id=interaction.guild_id,
                actor_discord_id=interaction.user.id,
                action="MANUAL_VERIFY",
                target_type="USER",
                target_id=str(user.id),
                details_json=f'{{"date": "{challenge_date}", "track": "{track}"}}',
            )
            session.add(log)
            await session.commit()

            streaks = await compute_user_streaks(db_user.id, session)
            await interaction.followup.send(
                f"✅ Manually verified {user.mention} for **{t.display_name}** on `{challenge_date}`! Streaks updated.",
                ephemeral=True,
            )

    @app_commands.command(name="admin_grace", description="[Owner] Mark an outage grace day to preserve streaks")
    @require_scope("config")
    async def admin_grace(
        self,
        interaction: discord.Interaction,
        grace_date: str,
        reason: str = "Bot or LeetCode outage",
    ):
        if not self.is_owner(interaction.user.id):
            await interaction.response.send_message("❌ Owner only command.", ephemeral=True)
            return

        try:
            g_date = datetime.strptime(grace_date, "%Y-%m-%d").date()
        except ValueError:
            await interaction.response.send_message("❌ Date format must be `YYYY-MM-DD`.", ephemeral=True)
            return

        async with async_session() as session:
            grace = OutageGraceDay(
                grace_date=g_date,
                track_id=None,  # All tracks
                reason=reason,
                created_by=interaction.user.id,
            )
            session.add(grace)
            await session.commit()

            await interaction.response.send_message(
                f"🛡️ **Grace Day Activated:** Date `{grace_date}` marked for all tracks. Streaks will not break for this date.",
                ephemeral=True,
            )

    @app_commands.command(name="admin_health", description="Check bot uptime, latency, and database status")
    @require_scope("config")
    async def admin_health(self, interaction: discord.Interaction):
        latency = round(self.bot.latency * 1000, 1)
        async with async_session() as session:
            from bot.db.models import DailyChallenge, Solve
            total_ch = (await session.execute(select(DailyChallenge))).scalars().all()
            total_solves = (await session.execute(select(Solve))).scalars().all()

        embed = discord.Embed(title="🏥 DSA_DAILY Bot Health", color=0x57F287)
        embed.add_field(name="Gateway Latency", value=f"`{latency}ms`", inline=True)
        embed.add_field(name="Database Status", value="`Connected (SQLite WAL)`", inline=True)
        embed.add_field(name="Scheduled Challenges", value=f"`{len(total_ch)}`", inline=True)
        embed.add_field(name="Total Solves Recorded", value=f"`{len(total_solves)}`", inline=True)
        embed.add_field(name="Guilds Joined", value=f"`{len(self.bot.guilds)}`", inline=True)
        embed.set_footer(text="All systems operational")
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(AdminCog(bot))
