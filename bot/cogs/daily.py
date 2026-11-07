import asyncio
from datetime import date, datetime, timezone
import discord
from discord.ext import commands, tasks
from sqlalchemy import select
from bot.db.session import async_session
from bot.db.models import ChannelSubscription, DailyPost, DailyChallenge, Track, GuildSettings, GuildTrackSettings
from bot.services.problems import problem_service
from bot.ui.embeds import create_daily_embed
from bot.ui.buttons import DailyChallengeView


class DailyCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.daily_post_loop.start()

    def cog_unload(self):
        self.daily_post_loop.cancel()

    @tasks.loop(minutes=1)
    async def daily_post_loop(self):
        now_utc = datetime.now(timezone.utc)
        # Trigger at 00:00 UTC
        if now_utc.hour == 0 and now_utc.minute == 0:
            await self.post_all_daily_challenges()

    @daily_post_loop.before_loop
    async def before_daily_post_loop(self):
        await self.bot.wait_until_ready()

    async def post_all_daily_challenges(self):
        today_utc = date.today()
        async with async_session() as session:
            # 1. Ensure challenges exist for Easy, Medium, Hard
            challenges = {}
            for slug in ["easy", "medium", "hard"]:
                ch = await problem_service.get_or_create_daily_challenge(slug, today_utc, session)
                challenges[slug] = ch

            # 2. Fetch all active subscriptions
            subs = (await session.execute(select(ChannelSubscription).where(ChannelSubscription.active == True))).scalars().all()

            for sub in subs:
                track = (await session.execute(select(Track).where(Track.id == sub.track_id))).scalar_one_or_none()
                if not track:
                    continue
                ch = challenges.get(track.slug)
                if not ch:
                    continue

                # Idempotency check: daily_posts(channel_id, challenge_id)
                existing_post = (
                    await session.execute(
                        select(DailyPost).where(
                            DailyPost.channel_id == sub.channel_id, DailyPost.challenge_id == ch.id
                        )
                    )
                ).scalar_one_or_none()

                if existing_post and existing_post.status == "posted":
                    continue

                channel = self.bot.get_channel(sub.channel_id)
                if not channel:
                    continue

                # Fetch custom track message or role ping
                gts = (
                    await session.execute(
                        select(GuildTrackSettings).where(
                            GuildTrackSettings.guild_id == sub.guild_id,
                            GuildTrackSettings.track_id == sub.track_id,
                        )
                    )
                ).scalar_one_or_none()

                content_parts = []
                if gts and gts.daily_message_text:
                    content_parts.append(gts.daily_message_text)
                if gts and gts.notification_role_id:
                    content_parts.append(f"<@&{gts.notification_role_id}>")

                msg_content = " ".join(content_parts) if content_parts else None

                embed = create_daily_embed(ch)
                view = DailyChallengeView(challenge_id=ch.id)

                try:
                    sent_msg = await channel.send(
                        content=msg_content,
                        embed=embed,
                        view=view,
                        allowed_mentions=discord.AllowedMentions(roles=True, everyone=False),
                    )

                    post_record = existing_post or DailyPost(
                        guild_id=sub.guild_id,
                        channel_id=sub.channel_id,
                        challenge_id=ch.id,
                    )
                    post_record.message_id = sent_msg.id
                    post_record.status = "posted"
                    post_record.posted_at = datetime.utcnow()
                    session.add(post_record)

                    # Check if thread discussions enabled
                    gs = (
                        await session.execute(
                            select(GuildSettings).where(GuildSettings.guild_id == sub.guild_id)
                        )
                    ).scalar_one_or_none()

                    if gs and gs.threads_enabled:
                        try:
                            thread = await sent_msg.create_thread(
                                name=f"DSA #{ch.challenge_number} — {track.display_name}",
                                auto_archive_duration=1440,
                            )
                            await thread.send(
                                "💡 Discussion space for today's challenge! Remember to use `||spoiler tags||` for solution codes."
                            )
                            post_record.thread_id = thread.id
                        except Exception:
                            pass

                    await session.commit()
                except Exception as e:
                    print(f"[DailyCog] Error posting to channel {sub.channel_id}: {e}")


async def setup(bot: commands.Bot):
    await bot.add_cog(DailyCog(bot))
