import json
import random
from datetime import date, timedelta
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from bot.db.models import Problem, DailyChallenge, Track


class ProblemService:
    async def get_or_create_daily_challenge(
        self, track_slug: str, challenge_date: date, session: AsyncSession
    ) -> DailyChallenge:
        # 1. Fetch track
        track_query = select(Track).where(Track.slug == track_slug)
        track = (await session.execute(track_query)).scalar_one_or_none()
        if not track:
            track = Track(slug=track_slug, display_name=track_slug.capitalize())
            session.add(track)
            await session.flush()

        # 2. Check if challenge already exists for date & track
        dc_query = select(DailyChallenge).where(
            and_(DailyChallenge.challenge_date == challenge_date, DailyChallenge.track_id == track.id)
        )
        existing = (await session.execute(dc_query)).scalar_one_or_none()
        if existing:
            return existing

        # 3. Determine challenge number (count of previous challenges in track + 1)
        prev_count_query = select(DailyChallenge).where(DailyChallenge.track_id == track.id)
        all_challenges = (await session.execute(prev_count_query)).scalars().all()
        next_num = len(all_challenges) + 1

        # 4. Fetch problems for this difficulty (90-day cooldown)
        diff_map = {"easy": "EASY", "medium": "MEDIUM", "hard": "HARD"}
        target_diff = diff_map.get(track_slug, "EASY")

        ninety_days_ago = challenge_date - timedelta(days=90)
        recent_pids = {
            c.problem_id
            for c in all_challenges
            if c.challenge_date and c.challenge_date >= ninety_days_ago
        }

        prob_query = select(Problem).where(
            and_(
                Problem.difficulty == target_diff,
                Problem.is_free == True,
                Problem.active == True,
            )
        )
        candidates = (await session.execute(prob_query)).scalars().all()
        valid_candidates = [p for p in candidates if p.id not in recent_pids]

        if not valid_candidates:
            # Fallback: if all were used in 90 days, select from all candidates
            valid_candidates = candidates

        if not valid_candidates:
            # Emergency dummy if pool has not been seeded yet
            dummy = Problem(
                leetcode_id="1",
                title_slug="two-sum",
                title="Two Sum",
                difficulty="EASY",
                topic_tags=json.dumps(["Array", "Hash Table"]),
                url="https://leetcode.com/problems/two-sum/",
                is_free=True,
                is_curated=True,
            )
            session.add(dummy)
            await session.flush()
            valid_candidates = [dummy]

        # Weighting: 3x preference for curated
        weighted_pool = []
        for p in valid_candidates:
            weight = 3 if p.is_curated else 1
            weighted_pool.extend([p] * weight)

        chosen_problem = random.choice(weighted_pool)

        # 5. Create challenge
        new_challenge = DailyChallenge(
            challenge_date=challenge_date,
            challenge_number=next_num,
            track_id=track.id,
            problem_id=chosen_problem.id,
            status="published",
        )
        session.add(new_challenge)
        await session.commit()
        return new_challenge


problem_service = ProblemService()
