import discord
from sqlalchemy import select
from bot.db.session import async_session
from bot.db.models import User, DailyChallenge, Solve, OverallStreak
from bot.services.verification import verification_service
from bot.ui.embeds import create_share_card_text


class DailyChallengeView(discord.ui.View):
    def __init__(self, challenge_id: int):
        super().__init__(timeout=None)
        self.challenge_id = challenge_id

    @discord.ui.button(
        label="Verify my solve",
        style=discord.ButtonStyle.primary,
        custom_id="btn_verify_solve",
        emoji="✅",
    )
    async def verify_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)

        async with async_session() as session:
            # Look up internal user
            user = (
                await session.execute(select(User).where(User.discord_id == interaction.user.id))
            ).scalar_one_or_none()

            if not user or user.link_status != "verified":
                await interaction.followup.send(
                    "⚠️ You haven't linked your LeetCode account yet!\nRun `/link username:<your_leetcode_handle>` to link in 10 seconds.",
                    ephemeral=True,
                )
                return

            result = await verification_service.verify_challenge_solve(
                user.id, self.challenge_id, session
            )

            await interaction.followup.send(result.message, ephemeral=True)

    @discord.ui.button(
        label="Share result",
        style=discord.ButtonStyle.secondary,
        custom_id="btn_share_result",
        emoji="📋",
    )
    async def share_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)

        async with async_session() as session:
            user = (
                await session.execute(select(User).where(User.discord_id == interaction.user.id))
            ).scalar_one_or_none()

            if not user:
                await interaction.followup.send("⚠️ Please link your account first with `/link`.", ephemeral=True)
                return

            # Fetch today's solves for this user across easy, medium, hard
            ch_query = select(DailyChallenge).where(DailyChallenge.id == self.challenge_id)
            ch = (await session.execute(ch_query)).scalar_one_or_none()
            if not ch:
                await interaction.followup.send("❌ Challenge not found.", ephemeral=True)
                return

            today_date = ch.challenge_date
            all_today_ch = (
                await session.execute(select(DailyChallenge).where(DailyChallenge.challenge_date == today_date))
            ).scalars().all()

            ch_map = {c.track_id: c.id for c in all_today_ch}

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

            card = create_share_card_text(ch.challenge_number, easy_s, med_s, hard_s, streak_val)
            msg = f"Here is your daily result card (copy & paste into chat):\n```text\n{card}\n```"
            await interaction.followup.send(msg, ephemeral=True)
