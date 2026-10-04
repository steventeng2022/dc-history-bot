"""Read local configuration without printing credentials."""

from dataclasses import dataclass, field
import os
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from dotenv import load_dotenv


@dataclass(frozen=True)
class Config:
    token: str = field(repr=False)
    timezone: str = "Asia/Taipei"
    database_path: Path = Path("data/history.db")
    guild_id: int | None = None
    log_level: str = "INFO"


def load_config() -> Config:
    load_dotenv()
    token = os.getenv("DISCORD_TOKEN", "").strip()
    if not token or token in {"your-bot-token-here", "貼上BotToken"}:
        raise ValueError("請先在 .env 設定 DISCORD_TOKEN；Token 請保存在本機。")

    timezone = os.getenv("DEFAULT_TIMEZONE", "Asia/Taipei").strip()
    try:
        ZoneInfo(timezone)
    except (ValueError, ZoneInfoNotFoundError):
        raise ValueError("DEFAULT_TIMEZONE 必須是有效時區，例如 Asia/Taipei。") from None

    guild_value = os.getenv("DISCORD_GUILD_ID", "").strip()
    guild_id = None
    if guild_value:
        if not guild_value.isascii() or not guild_value.isdecimal():
            raise ValueError("DISCORD_GUILD_ID 必須是伺服器的數字 ID，或留空。")
        guild_id = int(guild_value)
        if not 0 < guild_id < 2**64:
            raise ValueError("DISCORD_GUILD_ID 超出有效範圍。")

    log_level = os.getenv("LOG_LEVEL", "INFO").strip().upper()
    if log_level not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
        raise ValueError("LOG_LEVEL 請使用 DEBUG、INFO、WARNING、ERROR 或 CRITICAL。")

    database_value = os.getenv("DATABASE_PATH", "data/history.db").strip()
    if not database_value:
        raise ValueError("DATABASE_PATH 不可留空。")
    return Config(token, timezone, Path(database_value), guild_id, log_level)
