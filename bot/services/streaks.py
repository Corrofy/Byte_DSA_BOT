from datetime import date, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from bot.db.models import Solve, Streak, OverallStreak, OutageGraceDay, DailyChallenge


async def compute_user_streaks(user_id: int, session: AsyncSession) -> dict[str, Any]:
    # 1. Fetch all solved dates per track
    solves_query = (
        select(Solve.track_id, DailyChallenge.challenge_date)
        .join(DailyChallenge, Solve.challenge_id == DailyChallenge.id)
        .where(Solve.user_id == user_id)
        .order_by(DailyChallenge.challenge_date.asc())
    )
    res = await session.execute(solves_query)
    rows = res.all()

    # Fetch grace days
    grace_res = await session.execute(select(OutageGraceDay.grace_date, OutageGraceDay.track_id))
    grace_rows = grace_res.all()

    today_utc = date.today()
    yesterday_utc = today_utc - timedelta(days=1)

    # Group by track
    track_dates: dict[int, set[date]] = {1: set(), 2: set(), 3: set()}
    all_dates: set[date] = set()

    for track_id, cdate in rows:
        track_dates.setdefault(track_id, set()).add(cdate)
        all_dates.add(cdate)

    # Apply grace dates to track sets
    for gdate, gtrack in grace_rows:
        if gtrack is None:
            for t in track_dates:
                track_dates[t].add(gdate)
            all_dates.add(gdate)
        elif gtrack in track_dates:
            track_dates[gtrack].add(gdate)
            all_dates.add(gdate)

    def calculate_run(dates: set[date]) -> tuple[int, int, Optional[date]]:
        if not dates:
            return 0, 0, None
        sorted_dates = sorted(dates)
        runs = []
        current_run = 1
        for i in range(1, len(sorted_dates)):
            if sorted_dates[i] == sorted_dates[i - 1] + timedelta(days=1):
                current_run += 1
            else:
                runs.append(current_run)
                current_run = 1
        runs.append(current_run)
        longest = max(runs)

        last_date = sorted_dates[-1]
        # Current streak counts only if last date was today or yesterday
        if last_date >= yesterday_utc:
            current = current_run
        else:
            current = 0

        return current, longest, last_date

    # Update track streaks
    results = {}
    for track_id, dates in track_dates.items():
        curr, long, last_d = calculate_run(dates)
        results[track_id] = {"current": curr, "longest": long, "last_date": last_d}

        # Update or insert into streaks table
        st_query = select(Streak).where(Streak.user_id == user_id, Streak.track_id == track_id)
        st_row = (await session.execute(st_query)).scalar_one_or_none()
        if not st_row:
            st_row = Streak(user_id=user_id, track_id=track_id)
            session.add(st_row)
        st_row.current = curr
        st_row.longest = long
        st_row.last_challenge_date = last_d

    # Update overall streak
    o_curr, o_long, o_last_d = calculate_run(all_dates)
    results["overall"] = {"current": o_curr, "longest": o_long, "last_date": o_last_d}

    ost_query = select(OverallStreak).where(OverallStreak.user_id == user_id)
    ost_row = (await session.execute(ost_query)).scalar_one_or_none()
    if not ost_row:
        ost_row = OverallStreak(user_id=user_id)
        session.add(ost_row)
    ost_row.current = o_curr
    ost_row.longest = o_long
    ost_row.last_challenge_date = o_last_d

    await session.commit()
    return results
