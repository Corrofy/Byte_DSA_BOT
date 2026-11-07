"""
scope_guard.py — Channel-scope enforcement helpers for DSA_DAILY.

Usage in a cog command:
    from bot.utils.scope_guard import require_scope

    @app_commands.command(...)
    @require_scope("dsa_track")
    async def my_command(self, interaction: discord.Interaction, ...):
        ...

If a guild has NOT configured any scope (default state), ALL commands work
everywhere — zero friction until an admin explicitly opts in to scoped mode.

Once scope is configured, a command tagged with group "dsa_track" will only
run in channels that have "dsa_track" (or "all") in their channel_command_scopes
row for that guild. Otherwise the bot responds with a helpful ephemeral redirect.
"""

from __future__ import annotations

import functools
import logging
from typing import Callable

import discord
from discord import app_commands
from sqlalchemy import select

from bot.db.session import async_session
from bot.db.models import GuildScopeConfig, ChannelCommandScope

logger = logging.getLogger("dsa_daily.scope")

# Map command-group names to human-readable labels for user messages.
GROUP_LABELS: dict[str, str] = {
    "dsa_track": "DSA challenge commands",
    "leaderboard": "leaderboard commands",
    "config": "bot configuration commands",
    "all": "all commands",
}


async def _get_scope_config(guild_id: int):
    """Return (GuildScopeConfig | None, [ChannelCommandScope]) for a guild."""
    async with async_session() as session:
        cfg = (
            await session.execute(
                select(GuildScopeConfig).where(GuildScopeConfig.guild_id == guild_id)
            )
        ).scalar_one_or_none()

        if cfg is None:
            return None, []

        scopes = (
            await session.execute(
                select(ChannelCommandScope).where(ChannelCommandScope.guild_id == guild_id)
            )
        ).scalars().all()

        return cfg, list(scopes)


async def channel_is_allowed(guild_id: int, channel_id: int, command_group: str) -> tuple[bool, str | None]:
    """
    Check whether a command_group is permitted in a channel.

    Returns:
        (True, None)                  — allowed (or scope not configured yet)
        (False, redirect_channel_id)  — denied; redirect_channel_id may be set
                                        to a valid scoped channel for the group,
                                        or None if no valid channel is found.
    """
    cfg, scopes = await _get_scope_config(guild_id)

    # Scope not configured for this guild → allow everything.
    if cfg is None or not scopes:
        return True, None

    # Find scopes that match this channel.
    for scope in scopes:
        if scope.channel_id == channel_id:
            groups = [g.strip() for g in scope.command_group.split(",")]
            if command_group in groups or "all" in groups:
                return True, None

    # Channel not permitted — find a valid redirect channel for the group.
    redirect: str | None = None
    for scope in scopes:
        groups = [g.strip() for g in scope.command_group.split(",")]
        if command_group in groups or "all" in groups:
            redirect = str(scope.channel_id)
            break

    # Also check the designated special channels.
    if command_group == "leaderboard" and cfg.leaderboard_channel_id:
        redirect = str(cfg.leaderboard_channel_id)
    elif command_group == "config" and cfg.config_channel_id:
        redirect = str(cfg.config_channel_id)

    return False, redirect


def require_scope(command_group: str):
    """
    Decorator factory that enforces channel-scope rules before a command runs.

    Example:
        @require_scope("dsa_track")
        async def verify_cmd(self, interaction, ...): ...
    """

    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(self, interaction: discord.Interaction, *args, **kwargs):
            # DMs / guilds without IDs → pass through.
            if interaction.guild_id is None:
                await interaction.response.send_message(
                    "⚠️ This command can only be used inside a Discord server.",
                    ephemeral=True,
                )
                return

            allowed, redirect_id = await channel_is_allowed(
                interaction.guild_id, interaction.channel_id, command_group
            )

            if allowed:
                return await func(self, interaction, *args, **kwargs)

            # Build a helpful redirect message.
            label = GROUP_LABELS.get(command_group, command_group)
            if redirect_id:
                redirect_mention = f"<#{redirect_id}>"
                msg = (
                    f"🚫 **{label.capitalize()}** are not permitted in this channel.\n"
                    f"Please use them in {redirect_mention}."
                )
            else:
                msg = (
                    f"🚫 **{label.capitalize()}** are not permitted in this channel.\n"
                    f"Ask an admin to run `/scope channel add` to configure a designated channel."
                )

            await interaction.response.send_message(msg, ephemeral=True)

        return wrapper

    return decorator
