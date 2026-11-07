from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from bot.db.models import User, Streak, OverallStreak, Solve, GuildMember, Track


class LeaderboardEntry:
    def __init__(
        self,
        rank: int,
        discord_id: int,
        display_name: str,
        current_streak: int,
        longest_streak: int,
        total_solves: int,
        points: int,
    ):
        self.rank = rank
        self.discord_id = discord_id
        self.display_name = display_name
        self.current_streak = current_streak
        self.longest_streak = longest_streak
        self.total_solves = total_solves
        self.points = points


class LeaderboardService:
    async def get_track_leaderboard(
        self, track_slug: str, guild_id: int | None, session: AsyncSession, limit: int = 10
    ) -> list[LeaderboardEntry]:
        track_query = select(Track).where(Track.slug == track_slug)
        track = (await session.execute(track_query)).scalar_one_or_none()
        if not track:
            return []

        # Base query joining User, Streak, and Solves count
        stmt = (
            select(
                User.discord_id,
                User.leetcode_username,
                User.show_leetcode_username,
                Streak.current,
                Streak.longest,
                func.count(Solve.id).label("total_solves"),
            )
            .join(Streak, and_(Streak.user_id == User.id, Streak.track_id == track.id))
            .outerjoin(Solve, and_(Solve.user_id == User.id, Solve.track_id == track.id))
            .where(User.leaderboard_opt_out == False)
        )

        if guild_id:
            stmt = stmt.join(GuildMember, GuildMember.user_id == User.id).where(GuildMember.guild_id == guild_id)

        stmt = (
            stmt.group_by(User.id, Streak.current, Streak.longest)
            .order_by(Streak.current.desc(), Streak.longest.desc(), func.count(Solve.id).desc())
            .limit(limit)
        )

        rows = (await session.execute(stmt)).all()
        entries = []
        for rank, row in enumerate(rows, start=1):
            name = f"<@{row.discord_id}>"
            entries.append(
                LeaderboardEntry(
                    rank=rank,
                    discord_id=row.discord_id,
                    display_name=name,
                    current_streak=row.current,
                    longest_streak=row.longest,
                    total_solves=row.total_solves,
                    points=0,
                )
            )
        return entries

    async def get_overall_leaderboard(
        self, guild_id: int | None, session: AsyncSession, limit: int = 10
    ) -> list[LeaderboardEntry]:
        # Points: Easy = 1, Medium = 2, Hard = 3
        points_expr = func.sum(
            case(
                (Solve.track_id == 1, 1),
                (Solve.track_id == 2, 2),
                (Solve.track_id == 3, 3),
                else_=0,
            )
        ).label("points")

        from sqlalchemy import case

        stmt = (
            select(
                User.discord_id,
                OverallStreak.current,
                OverallStreak.longest,
                func.count(Solve.id).label("total_solves"),
                points_expr,
            )
            .outerjoin(OverallStreak, OverallStreak.user_id == User.id)
            .outerjoin(Solve, Solve.user_id == User.id)
            .where(User.leaderboard_opt_out == False)
        )

        if guild_id:
            stmt = stmt.join(GuildMember, GuildMember.user_id == User.id).where(GuildMember.guild_id == guild_id)

        stmt = (
            stmt.group_by(User.id, OverallStreak.current, OverallStreak.longest)
            .order_by(points_expr.desc().nullslast(), func.count(Solve.id).desc(), OverallStreak.current.desc())
            .limit(limit)
        )

        rows = (await session.execute(stmt)).all()
        entries = []
        for rank, row in enumerate(rows, start=1):
            name = f"<@{row.discord_id}>"
            entries.append(
                LeaderboardEntry(
                    rank=rank,
                    discord_id=row.discord_id,
                    display_name=name,
                    current_streak=row.current or 0,
                    longest_streak=row.longest or 0,
                    total_solves=row.total_solves or 0,
                    points=row.points or 0,
                )
            )
        return entries

    async def get_server_collective_streak(
        self, guild_id: int | None, session: AsyncSession
    ) -> dict[str, int]:
        from datetime import date, timedelta
        from bot.db.models import DailyChallenge, OutageGraceDay

        stmt = (
            select(DailyChallenge.challenge_date)
            .join(Solve, Solve.challenge_id == DailyChallenge.id)
            .distinct()
        )
        if guild_id:
            stmt = stmt.join(GuildMember, GuildMember.user_id == Solve.user_id).where(GuildMember.guild_id == guild_id)

        rows = (await session.execute(stmt)).scalars().all()
        dates = set(rows)

        # Include grace days
        grace_dates = (await session.execute(select(OutageGraceDay.grace_date))).scalars().all()
        dates.update(grace_dates)

        if not dates:
            return {"current": 0, "longest": 0, "total_active_days": 0}

        sorted_dates = sorted(dates)
        runs = []
        curr = 1
        for i in range(1, len(sorted_dates)):
            if sorted_dates[i] == sorted_dates[i - 1] + timedelta(days=1):
                curr += 1
            else:
                runs.append(curr)
                curr = 1
        runs.append(curr)

        today_utc = date.today()
        yesterday_utc = today_utc - timedelta(days=1)
        last_d = sorted_dates[-1]
        current_streak = curr if last_d >= yesterday_utc else 0

        return {
            "current": current_streak,
            "longest": max(runs),
            "total_active_days": len(sorted_dates),
        }


leaderboard_service = LeaderboardService()
