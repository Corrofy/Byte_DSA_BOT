import discord
import json
from bot.db.models import DailyChallenge

COLOR_MAP = {
    "EASY": 0x57F287,    # Discord Green
    "MEDIUM": 0xFEE75C,  # Discord Yellow/Gold
    "HARD": 0xED4245,    # Discord Red
}


def create_daily_embed(
    challenge: DailyChallenge,
    solved_count: int = 0,
    solvers: list[str] | None = None,
    show_solvers: bool = True,
) -> discord.Embed:
    problem = challenge.problem
    track_name = challenge.track.display_name if challenge.track else challenge.problem.difficulty.capitalize()
    color = COLOR_MAP.get(problem.difficulty.upper(), 0x5865F2)

    try:
        tags = json.loads(problem.topic_tags)
        tags_str = ", ".join(tags) if isinstance(tags, list) else str(tags)
    except Exception:
        tags_str = "Algorithms"

    desc = (
        f"### [{problem.title}]({problem.url})\n\n"
        f"**Difficulty:** `{problem.difficulty.capitalize()}`\n"
        f"**Topics:** `{tags_str}`\n"
        f"**Challenge:** `{track_name} #{challenge.challenge_number}`\n"
        f"**UTC Date:** `{challenge.challenge_date}`\n"
        f"**Solved Today:** `{solved_count}` solvers 🌟"
    )

    embed = discord.Embed(
        title=f"DSA_DAILY — {track_name} #{challenge.challenge_number}",
        description=desc,
        color=color,
    )

    # Wordle-style "Who was solving today" card section (no pings/mentions)
    if show_solvers and solvers and len(solvers) > 0:
        names_str = ", ".join(solvers[:8])
        if len(solvers) > 8:
            names_str += f" +{len(solvers) - 8} more"
        embed.add_field(
            name="👥 Solvers Today (Wordle-Style)",
            value=f"⚡ *{names_str}* solved today! Click **[Verify my solve]** below to join them.",
            inline=False,
        )

    embed.set_footer(text=f"DSA_DAILY • UTC day {challenge.challenge_date}")
    return embed


def create_share_card_text(challenge_num: int, easy_solved: bool, med_solved: bool, hard_solved: bool, streak: int) -> str:
    total_solved = sum([1 for s in [easy_solved, med_solved, hard_solved] if s])
    return (
        f"DSA_DAILY #{challenge_num}\n"
        f"Easy   {'✅' if easy_solved else '⬜'}\n"
        f"Medium {'✅' if med_solved else '⬜'}\n"
        f"Hard   {'✅' if hard_solved else '⬜'}\n"
        f"{total_solved}/3 solved · Streak {streak} 🔥"
    )
