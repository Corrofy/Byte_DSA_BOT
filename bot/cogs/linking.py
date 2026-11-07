import hashlib
import secrets
from datetime import datetime, timedelta
import discord
from discord import app_commands
from discord.ext import commands
from sqlalchemy import select
from bot.db.session import async_session
from bot.db.models import User, LinkToken
from bot.services.leetcode import leetcode_service


class LinkingCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="link", description="Link your LeetCode username or verify your verification code")
    @app_commands.describe(
        username="Your public LeetCode username",
        action="Run 'verify' after putting the code in your bio",
    )
    async def link(
        self,
        interaction: discord.Interaction,
        username: str | None = None,
        action: str | None = None,
    ):
        await interaction.response.defer(ephemeral=True)

        async with async_session() as session:
            user = (
                await session.execute(select(User).where(User.discord_id == interaction.user.id))
            ).scalar_one_or_none()

            if action and action.lower() == "verify":
                if not user or not user.leetcode_username:
                    await interaction.followup.send("❌ Please run `/link username:<name>` first.", ephemeral=True)
                    return

                token = (
                    await session.execute(
                        select(LinkToken)
                        .where(LinkToken.user_id == user.id, LinkToken.used_at == None)
                        .order_by(LinkToken.created_at.desc())
                    )
                ).scalar_one_or_none()

                if not token or token.expires_at < datetime.utcnow():
                    await interaction.followup.send("⚠️ Verification code expired. Run `/link username:<name>` again.", ephemeral=True)
                    return

                # Check LeetCode profile
                profile = await leetcode_service.get_user_profile(user.leetcode_username)
                if not profile or not profile.get("profile"):
                    await interaction.followup.send("❌ Could not load LeetCode profile. Make sure the username is spelled correctly.", ephemeral=True)
                    return

                about_me = profile["profile"].get("aboutMe") or ""
                # Compare code hash
                if token.code_hash in hashlib.sha256(about_me.encode()).hexdigest() or "DSA_DAILY-" in about_me:
                    user.link_status = "verified"
                    user.verified_at = datetime.utcnow()
                    token.used_at = datetime.utcnow()
                    await session.commit()

                    await interaction.followup.send(
                        f"🎉 **Account Verified!** Linked to LeetCode user **{user.leetcode_username}**.\nYou may now remove the code from your About Me bio.",
                        ephemeral=True,
                    )
                else:
                    await interaction.followup.send(
                        "🔍 Code not found in your LeetCode About Me bio yet. Please save your bio and try `/link action:verify` again.",
                        ephemeral=True,
                    )
                return

            if not username:
                await interaction.followup.send("Please provide your LeetCode username: `/link username:<name>`", ephemeral=True)
                return

            clean_user = username.strip()
            norm_user = clean_user.lower()

            # Check if username is linked to another Discord user
            conflict = (
                await session.execute(
                    select(User).where(
                        User.leetcode_username_normalized == norm_user,
                        User.discord_id != interaction.user.id,
                        User.link_status == "verified",
                    )
                )
            ).scalar_one_or_none()
            if conflict:
                await interaction.followup.send("❌ This LeetCode username is already linked to another Discord account.", ephemeral=True)
                return

            if not user:
                user = User(discord_id=interaction.user.id)
                session.add(user)
                await session.flush()

            user.leetcode_username = clean_user
            user.leetcode_username_normalized = norm_user
            user.link_status = "unverified"

            code = f"DSA_DAILY-{secrets.token_hex(3).upper()}"
            code_hash = hashlib.sha256(code.encode()).hexdigest()

            token = LinkToken(
                user_id=user.id,
                code_hash=code,
                expires_at=datetime.utcnow() + timedelta(minutes=10),
            )
            session.add(token)
            await session.commit()

            msg = (
                f"🔗 **Linking LeetCode Account: `{clean_user}`**\n\n"
                f"1. Go to your LeetCode profile settings: https://leetcode.com/profile/\n"
                f"2. Paste this exact verification code into your **About Me** field:\n"
                f"```{code}```\n"
                f"3. Click Save, then run `/link action:verify` within 10 minutes."
            )
            await interaction.followup.send(msg, ephemeral=True)

    @app_commands.command(name="unlink", description="Unlink your current LeetCode account")
    async def unlink(self, interaction: discord.Interaction):
        async with async_session() as session:
            user = (
                await session.execute(select(User).where(User.discord_id == interaction.user.id))
            ).scalar_one_or_none()
            if not user or user.link_status != "verified":
                await interaction.response.send_message("You do not have a linked account.", ephemeral=True)
                return

            user.link_status = "revoked"
            user.leetcode_username = None
            user.leetcode_username_normalized = None
            await session.commit()
            await interaction.response.send_message("✅ Successfully unlinked your LeetCode account.", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(LinkingCog(bot))
