"""
bot/cogs/scope.py — Channel-scope configuration commands for DSA_DAILY.

Admins use these commands to define WHERE the bot can operate and WHICH
commands are available in each channel.

Command structure:
  /scope set-role  role:@dsaBot          — Assign a Discord role to the bot
  /scope view                             — Summarise the current scope config
  /scope channel add    channel:#x  commands:<group>  — Grant a command group
  /scope channel remove channel:#x  commands:<group>  — Revoke a command group
  /scope channel set-config      channel:#dsa_config   — Mark private config channel
  /scope channel set-leaderboard channel:#dsa_leaderboard

Command groups (the `commands` parameter):
  dsa_track   → /verify, /link, /unlink, /subscribe, /unsubscribe,
                 /share, /profile, /streak, /help, /usage
  leaderboard → /leaderboard
  config      → /setup, /settings, /setmessage*, /admin_*, /scope
  all         → unrestricted for this channel
"""

from __future__ import annotations

import logging
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands
from sqlalchemy import select, delete

from bot.db.session import async_session
from bot.db.models import Guild, GuildScopeConfig, ChannelCommandScope, AuditLog

logger = logging.getLogger("dsa_daily.scope")

VALID_GROUPS = {"dsa_track", "leaderboard", "config", "all"}

GROUP_DESCRIPTIONS = {
    "dsa_track": "/verify, /link, /unlink, /subscribe, /unsubscribe, /share, /profile, /streak, /help, /usage",
    "leaderboard": "/leaderboard",
    "config": "/setup, /settings, /setmessage*, /admin_*, /scope",
    "all": "Unrestricted — all commands permitted",
}


class ScopeCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    scope_group = app_commands.Group(
        name="scope",
        description="[Admin] Configure the bot's channel and command scope",
    )
    scope_channel_group = app_commands.Group(
        name="channel",
        description="Configure per-channel command permissions",
        parent=scope_group,
    )

    # ------------------------------------------------------------------ #
    #  /scope set-role                                                     #
    # ------------------------------------------------------------------ #

    @scope_group.command(name="set-role", description="[Admin] Assign a Discord role that scopes the bot's access")
    @app_commands.describe(role="The Discord role to assign to Byte (the bot)")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def scope_set_role(self, interaction: discord.Interaction, role: discord.Role):
        """Assign a bounding role to the bot.

        In Discord, give this role only the channel permissions you want the bot
        to have. The bot will then respect those channel-level overwrites automatically.
        This command records the role in the database so `/scope view` can display it.
        """
        async with async_session() as session:
            await self._ensure_guild(session, interaction)
            cfg = await self._get_or_create_scope_cfg(session, interaction.guild_id)
            cfg.bot_role_id = role.id
            await session.commit()

        await interaction.response.send_message(
            f"✅ **Bot scope role set to {role.mention}.**\n\n"
            f"Now assign that role to Byte in Server Settings → Members, and use "
            f"channel permission overwrites to control which channels the bot can read/write.\n\n"
            f"Use `/scope channel add` to map command groups to specific channels.",
            ephemeral=True,
        )

    # ------------------------------------------------------------------ #
    #  /scope view                                                         #
    # ------------------------------------------------------------------ #

    @scope_group.command(name="view", description="[Admin] Show the current channel scope configuration")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def scope_view(self, interaction: discord.Interaction):
        async with async_session() as session:
            cfg = (
                await session.execute(
                    select(GuildScopeConfig).where(GuildScopeConfig.guild_id == interaction.guild_id)
                )
            ).scalar_one_or_none()

            if not cfg:
                await interaction.response.send_message(
                    "⚙️ **No scope configuration found.**\n"
                    "All commands are currently unrestricted (default open mode).\n\n"
                    "Use `/scope set-role` and `/scope channel add` to configure scoped access.",
                    ephemeral=True,
                )
                return

            scopes = (
                await session.execute(
                    select(ChannelCommandScope).where(ChannelCommandScope.guild_id == interaction.guild_id)
                )
            ).scalars().all()

        embed = discord.Embed(
            title="🔒 Bot Channel Scope Configuration",
            color=0x5865F2,
            description=(
                "This defines which commands are available in each channel.\n"
                "Commands used outside their designated channel will be blocked."
            ),
        )

        # Bot role
        if cfg.bot_role_id:
            embed.add_field(
                name="🎭 Bot Scope Role",
                value=f"<@&{cfg.bot_role_id}> (ID: `{cfg.bot_role_id}`)",
                inline=False,
            )
        else:
            embed.add_field(name="🎭 Bot Scope Role", value="*Not set — use `/scope set-role`*", inline=False)

        # Special channels
        special = []
        if cfg.config_channel_id:
            special.append(f"⚙️ **Config Channel:** <#{cfg.config_channel_id}> — `/setup`, `/settings`, `/admin_*`, `/scope`")
        if cfg.leaderboard_channel_id:
            special.append(f"🏆 **Leaderboard Channel:** <#{cfg.leaderboard_channel_id}> — `/leaderboard`")

        if special:
            embed.add_field(name="📌 Designated Channels", value="\n".join(special), inline=False)

        # Per-channel scopes
        if scopes:
            scope_lines = []
            for s in scopes:
                groups = s.command_group
                desc = " + ".join(GROUP_DESCRIPTIONS.get(g.strip(), g.strip()) for g in groups.split(","))
                scope_lines.append(f"<#{s.channel_id}> → `{groups}`")
            embed.add_field(name="📋 Channel Command Map", value="\n".join(scope_lines), inline=False)
        else:
            embed.add_field(
                name="📋 Channel Command Map",
                value="*No channel mappings yet. Use `/scope channel add` to configure.*",
                inline=False,
            )

        embed.set_footer(text="Use /scope channel add|remove to adjust permissions")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ------------------------------------------------------------------ #
    #  /scope channel add                                                  #
    # ------------------------------------------------------------------ #

    @scope_channel_group.command(name="add", description="[Admin] Allow a command group in a channel")
    @app_commands.describe(
        channel="The Discord channel to configure",
        commands="Command group: dsa_track | leaderboard | config | all",
    )
    @app_commands.choices(commands=[
        app_commands.Choice(name="dsa_track — /verify, /link, /subscribe, /help, /usage, /share, /profile, /streak", value="dsa_track"),
        app_commands.Choice(name="leaderboard — /leaderboard", value="leaderboard"),
        app_commands.Choice(name="config — /setup, /settings, /setmessage*, /admin_*, /scope", value="config"),
        app_commands.Choice(name="all — Unrestricted (all commands)", value="all"),
    ])
    @app_commands.checks.has_permissions(manage_guild=True)
    async def scope_channel_add(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
        commands: str,
    ):
        if commands not in VALID_GROUPS:
            await interaction.response.send_message(
                f"❌ Invalid command group `{commands}`. Choose: `dsa_track`, `leaderboard`, `config`, or `all`.",
                ephemeral=True,
            )
            return

        async with async_session() as session:
            await self._ensure_guild(session, interaction)
            await self._get_or_create_scope_cfg(session, interaction.guild_id)

            # Check if this exact mapping already exists.
            existing = (
                await session.execute(
                    select(ChannelCommandScope).where(
                        ChannelCommandScope.guild_id == interaction.guild_id,
                        ChannelCommandScope.channel_id == channel.id,
                        ChannelCommandScope.command_group == commands,
                    )
                )
            ).scalar_one_or_none()

            if existing:
                await interaction.response.send_message(
                    f"⚠️ {channel.mention} already has `{commands}` permissions.", ephemeral=True
                )
                return

            scope = ChannelCommandScope(
                guild_id=interaction.guild_id,
                channel_id=channel.id,
                command_group=commands,
            )
            session.add(scope)

            # Audit log
            log = AuditLog(
                guild_id=interaction.guild_id,
                actor_discord_id=interaction.user.id,
                action="SCOPE_CHANNEL_ADD",
                target_type="CHANNEL",
                target_id=str(channel.id),
                details_json=f'{{"command_group": "{commands}"}}',
            )
            session.add(log)
            await session.commit()

        group_desc = GROUP_DESCRIPTIONS.get(commands, commands)
        await interaction.response.send_message(
            f"✅ **Scope updated!** {channel.mention} now allows **`{commands}`** commands.\n"
            f"ℹ️ Covered commands: *{group_desc}*",
            ephemeral=True,
        )

    # ------------------------------------------------------------------ #
    #  /scope channel remove                                               #
    # ------------------------------------------------------------------ #

    @scope_channel_group.command(name="remove", description="[Admin] Remove a command group from a channel")
    @app_commands.describe(
        channel="The Discord channel to restrict",
        commands="Command group to remove: dsa_track | leaderboard | config | all",
    )
    @app_commands.choices(commands=[
        app_commands.Choice(name="dsa_track", value="dsa_track"),
        app_commands.Choice(name="leaderboard", value="leaderboard"),
        app_commands.Choice(name="config", value="config"),
        app_commands.Choice(name="all", value="all"),
    ])
    @app_commands.checks.has_permissions(manage_guild=True)
    async def scope_channel_remove(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
        commands: str,
    ):
        async with async_session() as session:
            deleted = await session.execute(
                delete(ChannelCommandScope).where(
                    ChannelCommandScope.guild_id == interaction.guild_id,
                    ChannelCommandScope.channel_id == channel.id,
                    ChannelCommandScope.command_group == commands,
                )
            )
            if deleted.rowcount == 0:
                await interaction.response.send_message(
                    f"⚠️ No `{commands}` scope found for {channel.mention}.", ephemeral=True
                )
                return

            log = AuditLog(
                guild_id=interaction.guild_id,
                actor_discord_id=interaction.user.id,
                action="SCOPE_CHANNEL_REMOVE",
                target_type="CHANNEL",
                target_id=str(channel.id),
                details_json=f'{{"command_group": "{commands}"}}',
            )
            session.add(log)
            await session.commit()

        await interaction.response.send_message(
            f"✅ Removed `{commands}` permissions from {channel.mention}.", ephemeral=True
        )

    # ------------------------------------------------------------------ #
    #  /scope channel set-config                                           #
    # ------------------------------------------------------------------ #

    @scope_channel_group.command(
        name="set-config",
        description="[Admin] Designate a private admin channel for bot configuration",
    )
    @app_commands.describe(channel="Private channel visible only to admins/mods and the bot")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def scope_set_config(self, interaction: discord.Interaction, channel: discord.TextChannel):
        async with async_session() as session:
            await self._ensure_guild(session, interaction)
            cfg = await self._get_or_create_scope_cfg(session, interaction.guild_id)
            cfg.config_channel_id = channel.id

            # Also auto-add "config" group to this channel.
            existing = (
                await session.execute(
                    select(ChannelCommandScope).where(
                        ChannelCommandScope.guild_id == interaction.guild_id,
                        ChannelCommandScope.channel_id == channel.id,
                        ChannelCommandScope.command_group == "config",
                    )
                )
            ).scalar_one_or_none()
            if not existing:
                session.add(ChannelCommandScope(
                    guild_id=interaction.guild_id,
                    channel_id=channel.id,
                    command_group="config",
                ))

            log = AuditLog(
                guild_id=interaction.guild_id,
                actor_discord_id=interaction.user.id,
                action="SCOPE_SET_CONFIG_CHANNEL",
                target_type="CHANNEL",
                target_id=str(channel.id),
                details_json="{}",
            )
            session.add(log)
            await session.commit()

        await interaction.response.send_message(
            f"⚙️ **Config channel set to** {channel.mention}.\n\n"
            f"All `/setup`, `/settings`, `/setmessage*`, `/admin_*`, and `/scope` commands "
            f"are now restricted to that channel (and any other channels with `config` scope).\n\n"
            f"**Recommended:** Set channel permissions so only admins and the bot can see it.",
            ephemeral=True,
        )

    # ------------------------------------------------------------------ #
    #  /scope channel set-leaderboard                                      #
    # ------------------------------------------------------------------ #

    @scope_channel_group.command(
        name="set-leaderboard",
        description="[Admin] Designate a channel as the leaderboard channel",
    )
    @app_commands.describe(channel="Channel where /leaderboard will be available")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def scope_set_leaderboard(self, interaction: discord.Interaction, channel: discord.TextChannel):
        async with async_session() as session:
            await self._ensure_guild(session, interaction)
            cfg = await self._get_or_create_scope_cfg(session, interaction.guild_id)
            cfg.leaderboard_channel_id = channel.id

            existing = (
                await session.execute(
                    select(ChannelCommandScope).where(
                        ChannelCommandScope.guild_id == interaction.guild_id,
                        ChannelCommandScope.channel_id == channel.id,
                        ChannelCommandScope.command_group == "leaderboard",
                    )
                )
            ).scalar_one_or_none()
            if not existing:
                session.add(ChannelCommandScope(
                    guild_id=interaction.guild_id,
                    channel_id=channel.id,
                    command_group="leaderboard",
                ))

            log = AuditLog(
                guild_id=interaction.guild_id,
                actor_discord_id=interaction.user.id,
                action="SCOPE_SET_LEADERBOARD_CHANNEL",
                target_type="CHANNEL",
                target_id=str(channel.id),
                details_json="{}",
            )
            session.add(log)
            await session.commit()

        await interaction.response.send_message(
            f"🏆 **Leaderboard channel set to** {channel.mention}.\n"
            f"`/leaderboard` is now scoped to that channel.",
            ephemeral=True,
        )

    # ------------------------------------------------------------------ #
    #  Private helpers                                                     #
    # ------------------------------------------------------------------ #

    async def _ensure_guild(self, session, interaction: discord.Interaction):
        g = (await session.execute(select(Guild).where(Guild.id == interaction.guild_id))).scalar_one_or_none()
        if not g:
            g = Guild(id=interaction.guild_id, name=interaction.guild.name)
            session.add(g)
            await session.flush()

    async def _get_or_create_scope_cfg(self, session, guild_id: int) -> GuildScopeConfig:
        cfg = (
            await session.execute(select(GuildScopeConfig).where(GuildScopeConfig.guild_id == guild_id))
        ).scalar_one_or_none()
        if not cfg:
            cfg = GuildScopeConfig(guild_id=guild_id)
            session.add(cfg)
            await session.flush()
        return cfg

    @scope_set_role.error
    @scope_view.error
    @scope_channel_add.error
    @scope_channel_remove.error
    @scope_set_config.error
    @scope_set_leaderboard.error
    async def scope_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(
                "❌ You need **Manage Server** permission to configure bot scope.", ephemeral=True
            )
        else:
            logger.exception("Scope command error", exc_info=error)
            await interaction.response.send_message(
                f"❌ An unexpected error occurred: `{error}`", ephemeral=True
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(ScopeCog(bot))
