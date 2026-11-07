import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    DISCORD_TOKEN: str = os.getenv("DISCORD_TOKEN", "")
    OWNER_DISCORD_ID: int = int(os.getenv("OWNER_DISCORD_ID", "0"))
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./data/dsa_daily.db")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LEETCODE_GRAPHQL_URL: str = os.getenv("LEETCODE_GRAPHQL_URL", "https://leetcode.com/graphql/")
    LEETCODE_USER_AGENT: str = os.getenv("LEETCODE_USER_AGENT", "DSA_DAILY/1.0 (Discord Bot)")
    BACKUP_DIR: str = os.getenv("BACKUP_DIR", "./backups")
    DAILY_POST_HOUR_UTC: int = int(os.getenv("DAILY_POST_HOUR_UTC", "0"))
    RECAP_HOUR_UTC: int = int(os.getenv("RECAP_HOUR_UTC", "18"))
    DEV_MODE: bool = os.getenv("DEV_MODE", "false").lower() in ("true", "1", "yes", "t")
    DEV_GUILD_ID: int | None = int(os.getenv("DEV_GUILD_ID")) if os.getenv("DEV_GUILD_ID") else None


settings = Settings()
