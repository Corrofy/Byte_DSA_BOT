from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from bot.db.models import User, DailyChallenge, Solve
from bot.services.leetcode import leetcode_service
from bot.services.streaks import compute_user_streaks


class VerificationResult:
    def __init__(self, success: bool, message: str, solve: Optional[Solve] = None, streak_info: Optional[dict] = None):
        self.success = success
        self.message = message
        self.solve = solve
        self.streak_info = streak_info


class VerificationService:
    async def verify_challenge_solve(
        self, user_id: int, challenge_id: int, session: AsyncSession
    ) -> VerificationResult:
        # 1. Fetch user
        user = (await session.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
        if not user or user.link_status != "verified" or not user.leetcode_username:
            return VerificationResult(
                False, "⚠️ Your LeetCode account is not linked. Use `/link username:<name>` to link your account."
            )

        # 2. Fetch challenge
        ch_query = select(DailyChallenge).where(DailyChallenge.id == challenge_id)
        challenge = (await session.execute(ch_query)).scalar_one_or_none()
        if not challenge:
            return VerificationResult(False, "❌ Daily challenge not found.")

        # Check if already solved
        existing_solve = (
            await session.execute(
                select(Solve).where(and_(Solve.user_id == user_id, Solve.challenge_id == challenge_id))
            )
        ).scalar_one_or_none()

        if existing_solve:
            streaks = await compute_user_streaks(user_id, session)
            return VerificationResult(
                True,
                f"✅ You have already verified this challenge on {existing_solve.solved_at.strftime('%Y-%m-%d %H:%M UTC')}!",
                existing_solve,
                streaks,
            )

        # 3. Query LeetCode recent accepted submissions
        submissions = await leetcode_service.get_recent_accepted_submissions(user.leetcode_username, limit=20)
        if not submissions:
            return VerificationResult(
                False,
                "⚠️ No recent accepted submissions found. Ensure your LeetCode submission history is set to **Public** in your LeetCode Privacy Settings.",
            )

        # 4. Check for matching problem titleSlug & UTC challenge day
        # UTC challenge day range: [challenge_date 00:00:00 UTC, challenge_date + 24h)
        target_slug = challenge.problem.title_slug
        c_date = challenge.challenge_date

        matched_sub = None
        for sub in submissions:
            if sub.get("titleSlug") == target_slug and sub.get("statusDisplay") == "Accepted":
                ts = int(sub.get("timestamp", 0))
                sub_dt = datetime.fromtimestamp(ts, tz=timezone.utc)
                if sub_dt.date() == c_date:
                    matched_sub = sub
                    break

        if not matched_sub:
            return VerificationResult(
                False,
                f"🔍 No accepted submission found for **{challenge.problem.title}** on UTC date `{c_date}`. Make sure you solved it today and that your submission is among your 20 most recent accepted solutions.",
            )

        # 5. Record solve
        ts = int(matched_sub.get("timestamp", 0))
        sub_dt = datetime.fromtimestamp(ts, tz=timezone.utc).replace(tzinfo=None)

        new_solve = Solve(
            user_id=user_id,
            challenge_id=challenge_id,
            track_id=challenge.track_id,
            leetcode_submission_id=str(matched_sub.get("id")),
            solved_at=sub_dt,
            language=matched_sub.get("lang", "unknown"),
            verification_method="auto",
            verified_at=datetime.utcnow(),
        )
        session.add(new_solve)
        await session.commit()

        # 6. Recompute streaks
        streak_info = await compute_user_streaks(user_id, session)

        return VerificationResult(
            True,
            f"🎉 Verified! Solved with **{matched_sub.get('lang')}**. Track streak is now `{streak_info.get(challenge.track_id, {}).get('current', 1)}` 🔥!",
            new_solve,
            streak_info,
        )


verification_service = VerificationService()
