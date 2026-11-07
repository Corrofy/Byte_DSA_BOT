import discord
from discord import app_commands
from discord.ext import commands
from sqlalchemy import select, func
from bot.db.session import async_session
from bot.db.models import User, Streak, OverallStreak, Solve, GuildTrackSettings, Track
from bot.utils.scope_guard import require_scope


class StatsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="profile", description="View your or another user's DSA_DAILY profile & streaks")
    @require_scope("dsa_track")
    async def profile(self, interaction: discord.Interaction, user: discord.Member | None = None):
        target = user or interaction.user
        await interaction.response.defer()

        async with async_session() as session:
            db_user = (
                await session.execute(select(User).where(User.discord_id == target.id))
            ).scalar_one_or_none()

            if not db_user or db_user.link_status != "verified":
                await interaction.followup.send(f"⚠️ {target.display_name} has not linked their LeetCode account yet.")
                return

            # Overall streak
            ost = (
                await session.execute(select(OverallStreak).where(OverallStreak.user_id == db_user.id))
            ).scalar_one_or_none()

            # Track streaks
            streaks = (
                await session.execute(select(Streak).where(Streak.user_id == db_user.id))
            ).scalars().all()
            streak_map = {s.track_id: s for s in streaks}

            # Solves breakdown
            total_solves = (
                await session.execute(select(func.count(Solve.id)).where(Solve.user_id == db_user.id))
            ).scalar() or 0

            # Language breakdown
            langs = (
                await session.execute(
                    select(Solve.language, func.count(Solve.id))
                    .where(Solve.user_id == db_user.id)
                    .group_by(Solve.language)
                )
            ).all()

            lang_str = ", ".join([f"{l[0]} ({l[1]})" for l in langs]) if langs else "None yet"

            embed = discord.Embed(
                title=f"DSA_DAILY Profile — {target.display_name}",
                color=0x5865F2,
            )
            embed.set_thumbnail(url=target.display_avatar.url)

            lc_display = db_user.leetcode_username if db_user.show_leetcode_username else "*(Hidden)*"
            embed.add_field(name="LeetCode Account", value=f"`{lc_display}`", inline=True)
            embed.add_field(name="Overall Streak", value=f"`{ost.current if ost else 0}` 🔥 (Longest: `{ost.longest if ost else 0}`)", inline=True)
            embed.add_field(name="Total Solves", value=f"`{total_solves}`", inline=True)

            # Tracks
            e_st = streak_map.get(1)
            m_st = streak_map.get(2)
            h_st = streak_map.get(3)

            track_info = (
                f"🟢 **Easy:** Streak `{e_st.current if e_st else 0}` (Best: `{e_st.longest if e_st else 0}`)\n"
                f"🟡 **Medium:** Streak `{m_st.current if m_st else 0}` (Best: `{m_st.longest if m_st else 0}`)\n"
                f"🔴 **Hard:** Streak `{h_st.current if h_st else 0}` (Best: `{h_st.longest if h_st else 0}`)"
            )
            embed.add_field(name="Track Streaks", value=track_info, inline=False)
            embed.add_field(name="Languages Used", value=lang_str, inline=False)
            embed.set_footer(text="Stats tracked from official DSA_DAILY solves • Strict daily UTC reset")

            await interaction.followup.send(embed=embed)

    @app_commands.command(name="streak", description="Quick view of your current active streak")
    @require_scope("dsa_track")
    async def streak(self, interaction: discord.Interaction):
        async with async_session() as session:
            db_user = (
                await session.execute(select(User).where(User.discord_id == interaction.user.id))
            ).scalar_one_or_none()

            if not db_user or db_user.link_status != "verified":
                await interaction.response.send_message("⚠️ Link your LeetCode account with `/link` first.", ephemeral=True)
                return

            ost = (
                await session.execute(select(OverallStreak).where(OverallStreak.user_id == db_user.id))
            ).scalar_one_or_none()

            curr = ost.current if ost else 0
            best = ost.longest if ost else 0

            await interaction.response.send_message(
                f"🔥 **Your DSA_DAILY Streak:** `{curr}` days (Personal Record: `{best}` days)", ephemeral=True
            )

    @app_commands.command(name="subscribe", description="Self-assign daily notification role for a difficulty track")
    async def subscribe(self, interaction: discord.Interaction, track: str):
        track_slug = track.lower().strip()
        async with async_session() as session:
            t = (await session.execute(select(Track).where(Track.slug == track_slug))).scalar_one_or_none()
            if not t:
                await interaction.response.send_message("❌ Choose `easy`, `medium`, or `hard`.", ephemeral=True)
                return

            gts = (
                await session.execute(
                    select(GuildTrackSettings).where(
                        GuildTrackSettings.guild_id == interaction.guild_id, GuildTrackSettings.track_id == t.id
                    )
                )
            ).scalar_one_or_none()

            if not gts or not gts.notification_role_id:
                await interaction.response.send_message(
                    f"⚠️ The server admin has not set up a ping role for {track_slug} yet.", ephemeral=True
                )
                return

            role = interaction.guild.get_role(gts.notification_role_id)
            if not role:
                await interaction.response.send_message("❌ Role not found on this server.", ephemeral=True)
                return

            try:
                await interaction.user.add_roles(role)
                await interaction.response.send_message(f"✅ Subscribed to daily {t.display_name} notifications ({role.mention})!", ephemeral=True)
            except discord.Forbidden:
                await interaction.response.send_message("❌ Bot lacks permission to assign that role. Please check role hierarchy.", ephemeral=True)

    @app_commands.command(name="privacy", description="Control your leaderboard privacy and visibility")
    async def privacy(
        self,
        interaction: discord.Interaction,
        leaderboard: bool | None = None,
        leetcode: bool | None = None,
    ):
        async with async_session() as session:
            user = (
                await session.execute(select(User).where(User.discord_id == interaction.user.id))
            ).scalar_one_or_none()
            if not user:
                await interaction.response.send_message("You do not have a linked account.", ephemeral=True)
                return

            if leaderboard is not None:
                user.leaderboard_opt_out = not leaderboard
            if leetcode is not None:
                user.show_leetcode_username = leetcode

            await session.commit()
            await interaction.response.send_message(
                f"🔒 **Privacy Updated:**\n"
                f"• Leaderboard: `{'Visible' if not user.leaderboard_opt_out else 'Hidden (Opted out)'}`\n"
                f"• Show LeetCode Username: `{'Yes' if user.show_leetcode_username else 'Hidden'}`",
                ephemeral=True,
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(StatsCog(bot))
