import discord
from discord import app_commands
from discord.ext import commands
from sqlalchemy import select
from bot.db.session import async_session
from bot.db.models import Guild, GuildSettings, ChannelSubscription, Track, GuildTrackSettings
from bot.utils.scope_guard import require_scope


class SetupCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="setup", description="Bind a channel to a difficulty track (easy, medium, hard)")
    @app_commands.checks.has_permissions(manage_guild=True)
    @require_scope("config")
    async def setup(
        self,
        interaction: discord.Interaction,
        track: str,
        channel: discord.TextChannel,
    ):
        track_slug = track.lower().strip()
        if track_slug not in ["easy", "medium", "hard"]:
            await interaction.response.send_message("❌ Track must be `easy`, `medium`, or `hard`.", ephemeral=True)
            return

        async with async_session() as session:
            # Ensure guild exists
            g = (await session.execute(select(Guild).where(Guild.id == interaction.guild_id))).scalar_one_or_none()
            if not g:
                g = Guild(id=interaction.guild_id, name=interaction.guild.name)
                session.add(g)

            # Ensure track exists
            t = (await session.execute(select(Track).where(Track.slug == track_slug))).scalar_one_or_none()
            if not t:
                t = Track(slug=track_slug, display_name=track_slug.capitalize())
                session.add(t)
                await session.flush()

            # Check if channel is already bound
            existing_sub = (
                await session.execute(select(ChannelSubscription).where(ChannelSubscription.channel_id == channel.id))
            ).scalar_one_or_none()
            if existing_sub:
                await interaction.response.send_message(
                    f"❌ Channel {channel.mention} is already bound to a track. Use `/setup remove` first.", ephemeral=True
                )
                return

            # Check if track is already bound in this guild
            track_sub = (
                await session.execute(
                    select(ChannelSubscription).where(
                        ChannelSubscription.guild_id == interaction.guild_id,
                        ChannelSubscription.track_id == t.id,
                    )
                )
            ).scalar_one_or_none()
            if track_sub:
                await interaction.response.send_message(
                    f"❌ Track `{track_slug}` is already bound to another channel in this server.", ephemeral=True
                )
                return

            sub = ChannelSubscription(guild_id=interaction.guild_id, channel_id=channel.id, track_id=t.id)
            session.add(sub)
            await session.commit()

            # Send test confirmation message in target channel
            try:
                await channel.send(
                    f"🎉 **DSA_DAILY Active!** This channel will receive daily **{t.display_name}** challenges at 00:00 UTC."
                )
            except discord.Forbidden:
                pass

            await interaction.response.send_message(
                f"✅ Successfully bound `{track_slug}` track to {channel.mention}!", ephemeral=True
            )

    @app_commands.command(name="settings", description="Configure thread discussions, weekly recap, and Wordle-style solver card")
    @app_commands.checks.has_permissions(manage_guild=True)
    @require_scope("config")
    async def settings(
        self,
        interaction: discord.Interaction,
        threads: bool | None = None,
        recap_channel: discord.TextChannel | None = None,
        show_solvers: bool | None = None,
    ):
        async with async_session() as session:
            gs = (
                await session.execute(select(GuildSettings).where(GuildSettings.guild_id == interaction.guild_id))
            ).scalar_one_or_none()
            if not gs:
                gs = GuildSettings(guild_id=interaction.guild_id)
                session.add(gs)

            changes = []
            if threads is not None:
                gs.threads_enabled = threads
                changes.append(f"• Discussion Threads: `{'Enabled' if threads else 'Disabled'}`")
            if recap_channel is not None:
                gs.recap_channel_id = recap_channel.id
                gs.recap_enabled = True
                changes.append(f"• Weekly Recap Channel: {recap_channel.mention}")
            if show_solvers is not None:
                gs.show_solvers_enabled = show_solvers
                changes.append(f"• Wordle-Style Solvers Card: `{'Enabled' if show_solvers else 'Disabled'}`")

            await session.commit()
            await interaction.response.send_message(
                "⚙️ **Server Settings Updated:**\n" + ("\n".join(changes) if changes else "No changes made."),
                ephemeral=True,
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(SetupCog(bot))
