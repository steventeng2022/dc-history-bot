"""Run with python -m history_bot."""

import asyncio
import logging
import sys

import aiohttp
import discord

from .bot import HistoryBot
from .config import load_config


async def run() -> None:
    config = load_config()
    logging.basicConfig(
        level=config.log_level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    async with HistoryBot(config) as bot:
        await bot.start(config.token)


def main() -> None:
    try:
        asyncio.run(run())
    except ValueError as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1) from None
    except discord.LoginFailure:
        print("Discord Token 無效，請在 Developer Portal 重設後更新 .env。", file=sys.stderr)
        raise SystemExit(1) from None
    except (discord.HTTPException, aiohttp.ClientError, OSError) as error:
        print(f"啟動失敗（{type(error).__name__}）；請確認 Discord 連線與本機資料目錄權限。", file=sys.stderr)
        raise SystemExit(1) from None
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
