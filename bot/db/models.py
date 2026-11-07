from datetime import datetime, date
from typing import Optional
from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Guild(Base):
    __tablename__ = "guilds"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    joined_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    settings: Mapped[Optional["GuildSettings"]] = relationship(back_populates="guild", uselist=False)
    track_settings: Mapped[list["GuildTrackSettings"]] = relationship(back_populates="guild")
    subscriptions: Mapped[list["ChannelSubscription"]] = relationship(back_populates="guild")


class GuildSettings(Base):
    __tablename__ = "guild_settings"

    guild_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("guilds.id"), primary_key=True)
    threads_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    recap_channel_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    recap_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    recap_message_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    recap_hour_utc: Mapped[int] = mapped_column(Integer, default=18)
    show_solvers_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    guild: Mapped["Guild"] = relationship(back_populates="settings")


class Track(Base):
    __tablename__ = "tracks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    slug: Mapped[str] = mapped_column(String(32), unique=True, index=True)  # easy, medium, hard
    display_name: Mapped[str] = mapped_column(String(64))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class GuildTrackSettings(Base):
    __tablename__ = "guild_track_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guild_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("guilds.id"))
    track_id: Mapped[int] = mapped_column(Integer, ForeignKey("tracks.id"))
    daily_message_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notification_role_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    guild: Mapped["Guild"] = relationship(back_populates="track_settings")
    track: Mapped["Track"] = relationship()

    __table_args__ = (
        UniqueConstraint("guild_id", "track_id", name="uq_guild_track_settings"),
    )


class ChannelSubscription(Base):
    __tablename__ = "channel_subscriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guild_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("guilds.id"))
    channel_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    track_id: Mapped[int] = mapped_column(Integer, ForeignKey("tracks.id"))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    guild: Mapped["Guild"] = relationship(back_populates="subscriptions")
    track: Mapped["Track"] = relationship()

    __table_args__ = (
        UniqueConstraint("guild_id", "track_id", name="uq_channel_sub_guild_track"),
    )


class Problem(Base):
    __tablename__ = "problems"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    leetcode_id: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    title_slug: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(255))
    difficulty: Mapped[str] = mapped_column(String(16))  # EASY, MEDIUM, HARD
    topic_tags: Mapped[str] = mapped_column(Text)  # JSON serialized array of tags
    url: Mapped[str] = mapped_column(String(255))
    is_free: Mapped[bool] = mapped_column(Boolean, default=True)
    is_curated: Mapped[bool] = mapped_column(Boolean, default=False)
    source: Mapped[str] = mapped_column(String(64), default="leetcode")
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    metadata_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DailyChallenge(Base):
    __tablename__ = "daily_challenges"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    challenge_date: Mapped[date] = mapped_column(Date, index=True)
    challenge_number: Mapped[int] = mapped_column(Integer)
    track_id: Mapped[int] = mapped_column(Integer, ForeignKey("tracks.id"))
    problem_id: Mapped[int] = mapped_column(Integer, ForeignKey("problems.id"))
    status: Mapped[str] = mapped_column(String(32), default="scheduled")  # scheduled, published, cancelled
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    track: Mapped["Track"] = relationship()
    problem: Mapped["Problem"] = relationship()

    __table_args__ = (
        UniqueConstraint("challenge_date", "track_id", name="uq_challenge_date_track"),
        UniqueConstraint("track_id", "challenge_number", name="uq_track_challenge_number"),
    )


class DailyPost(Base):
    __tablename__ = "daily_posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guild_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("guilds.id"), index=True)
    channel_id: Mapped[int] = mapped_column(BigInteger, index=True)
    challenge_id: Mapped[int] = mapped_column(Integer, ForeignKey("daily_challenges.id"), index=True)
    message_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    thread_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="pending")  # pending, posted, failed, skipped
    posted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    challenge: Mapped["DailyChallenge"] = relationship()

    __table_args__ = (
        UniqueConstraint("channel_id", "challenge_id", name="uq_channel_challenge_post"),
    )


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    discord_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    leetcode_username: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    leetcode_username_normalized: Mapped[Optional[str]] = mapped_column(String(128), unique=True, nullable=True, index=True)
    link_status: Mapped[str] = mapped_column(String(32), default="unverified")  # unverified, verified, revoked
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    leaderboard_opt_out: Mapped[bool] = mapped_column(Boolean, default=False)
    show_leetcode_username: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_seen_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class LinkToken(Base):
    __tablename__ = "link_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), index=True)
    code_hash: Mapped[str] = mapped_column(String(128))
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    used_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class GuildMember(Base):
    __tablename__ = "guild_members"

    guild_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), primary_key=True)
    joined_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_seen_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class Solve(Base):
    __tablename__ = "solves"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), index=True)
    challenge_id: Mapped[int] = mapped_column(Integer, ForeignKey("daily_challenges.id"), index=True)
    track_id: Mapped[int] = mapped_column(Integer, ForeignKey("tracks.id"), index=True)
    leetcode_submission_id: Mapped[str] = mapped_column(String(64))
    solved_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    language: Mapped[str] = mapped_column(String(64))
    verification_method: Mapped[str] = mapped_column(String(32), default="auto")  # auto, manual
    verified_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    verified_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    evidence: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship()
    challenge: Mapped["DailyChallenge"] = relationship()
    track: Mapped["Track"] = relationship()

    __table_args__ = (
        UniqueConstraint("user_id", "challenge_id", name="uq_user_challenge_solve"),
        UniqueConstraint("user_id", "leetcode_submission_id", name="uq_user_submission_solve"),
    )


class Streak(Base):
    __tablename__ = "streaks"

    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), primary_key=True)
    track_id: Mapped[int] = mapped_column(Integer, ForeignKey("tracks.id"), primary_key=True)
    current: Mapped[int] = mapped_column(Integer, default=0)
    longest: Mapped[int] = mapped_column(Integer, default=0)
    last_challenge_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user: Mapped["User"] = relationship()
    track: Mapped["Track"] = relationship()


class OverallStreak(Base):
    __tablename__ = "overall_streaks"

    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), primary_key=True)
    current: Mapped[int] = mapped_column(Integer, default=0)
    longest: Mapped[int] = mapped_column(Integer, default=0)
    last_challenge_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user: Mapped["User"] = relationship()


class RecapPost(Base):
    __tablename__ = "recap_posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guild_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("guilds.id"))
    week_start: Mapped[date] = mapped_column(Date)
    message_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="pending")
    posted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    __table_args__ = (
        UniqueConstraint("guild_id", "week_start", name="uq_recap_guild_week"),
    )


class OutageGraceDay(Base):
    __tablename__ = "outage_grace_days"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    grace_date: Mapped[date] = mapped_column(Date, index=True)
    track_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("tracks.id"), nullable=True)
    reason: Mapped[str] = mapped_column(String(255))
    created_by: Mapped[int] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class GuildScopeConfig(Base):
    """Defines the bot's overall scope within a guild — which role it wears and which
    channels are designated for config and leaderboard use."""

    __tablename__ = "guild_scope_config"

    guild_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    # Discord role ID assigned to the bot to gate channel access
    bot_role_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    # Private admin/moderator channel for bot configuration commands
    config_channel_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    # Dedicated leaderboard channel
    leaderboard_channel_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    channel_scopes: Mapped[list["ChannelCommandScope"]] = relationship(
        back_populates="guild_scope", cascade="all, delete-orphan"
    )


class ChannelCommandScope(Base):
    """Maps a specific Discord channel to one or more command groups that are
    permitted in that channel.

    command_group values:
      - 'dsa_track'   : /verify, /link, /unlink, /subscribe, /unsubscribe,
                        /share, /profile, /streak, /help, /usage
      - 'leaderboard' : /leaderboard
      - 'config'      : /setup, /settings, /setmessage*, /admin_*, /scope
      - 'all'         : unrestricted (scope enforcement disabled for this channel)
    """

    __tablename__ = "channel_command_scopes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guild_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("guild_scope_config.guild_id"), index=True)
    channel_id: Mapped[int] = mapped_column(BigInteger, index=True)
    # Comma-separated list of groups, e.g. "dsa_track" or "dsa_track,leaderboard"
    command_group: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    guild_scope: Mapped["GuildScopeConfig"] = relationship(back_populates="channel_scopes")

    __table_args__ = (
        UniqueConstraint("guild_id", "channel_id", "command_group", name="uq_channel_command_scope"),
    )


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guild_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True, index=True)
    actor_discord_id: Mapped[int] = mapped_column(BigInteger)
    action: Mapped[str] = mapped_column(String(64))
    target_type: Mapped[str] = mapped_column(String(64))
    target_id: Mapped[str] = mapped_column(String(64))
    details_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
