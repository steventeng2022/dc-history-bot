"""Preview a Discord embed without connecting to Discord."""

import argparse
import asyncio
from datetime import datetime
import json
import sys
from zoneinfo import ZoneInfo

import aiohttp

from .formatting import build_embed
from .history import Category, HistoryClient, HistoryError, HistoryItem, HistoryResult, source_url, validate_date


async def preview(args: argparse.Namespace) -> dict:
    if args.demo:
        result = HistoryResult(
            month=10,
            day=4,
            category=Category.EVENTS,
            items=(HistoryItem("1957年", "蘇聯發射史普尼克1號，為人類首顆人造衛星。"),),
            source_url=source_url(10, 4),
        )
        embed = build_embed(result, args.count)
        embed.title = f"【離線示範】{embed.title}"
        return embed.to_dict()
    now = datetime.now(ZoneInfo("Asia/Taipei"))
    if (args.month is None) != (args.day is None):
        raise ValueError("請同時指定 --month 與 --day。")
    month = args.month if args.month is not None else now.month
    day = args.day if args.day is not None else now.day
    validate_date(month, day)
    async with aiohttp.ClientSession(
        timeout=aiohttp.ClientTimeout(total=20),
        trust_env=True,
        headers={"User-Agent": "HistoryTodayDiscordBot/1.0 (educational date lookup; Python/aiohttp)"},
    ) as session:
        result = await HistoryClient(session).get(month, day, Category(args.category))
        return build_embed(result, args.count).to_dict()


def main() -> None:
    parser = argparse.ArgumentParser(description="預覽歷史 Discord 訊息的 embed JSON；不需 Discord Token。")
    parser.add_argument("--demo", action="store_true", help="離線示範，固定顯示 10 月 4 日的一則大事記")
    parser.add_argument("--month", type=int)
    parser.add_argument("--day", type=int)
    parser.add_argument("--category", choices=[category.value for category in Category], default="events")
    parser.add_argument("--count", type=int, choices=range(1, 11), default=5)
    args = parser.parse_args()
    if args.demo and (args.month is not None or args.day is not None or args.category != "events"):
        parser.error("--demo 使用固定示範日期與分類，請省略 --month、--day 及 --category。")
    try:
        print(json.dumps(asyncio.run(preview(args)), ensure_ascii=False, indent=2))
    except (ValueError, HistoryError) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
