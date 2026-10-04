from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, Mock, patch

import discord
from discord import app_commands
from discord.utils import maybe_coroutine

from history_bot.bot import HistoryBot
from history_bot.config import Config
from history_bot.formatting import build_embed
from history_bot.history import Category, HistoryError, HistoryItem, HistoryResult, source_url


def interaction():
    return SimpleNamespace(
        response=SimpleNamespace(
            send_message=AsyncMock(), defer=AsyncMock(), is_done=Mock(return_value=False)
        ),
        edit_original_response=AsyncMock(),
        permissions=discord.Permissions.none(),
        guild_id=123,
    )


class BotTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.bot = HistoryBot(Config("offline-test", database_path=Path(":memory:")))

    async def asyncTearDown(self):
        await self.bot.close()

    async def test_discord_accepts_commands_and_parameter_constraints(self):
        self.assertEqual(
            {command.name for command in self.bot.tree.get_commands()},
            {"today", "daily", "daily-status", "daily-off", "help"},
        )
        params = {parameter.name: parameter for parameter in self.bot.tree.get_command("today").parameters}
        self.assertEqual((params["count"].min_value, params["count"].max_value), (1, 10))
        self.assertEqual((params["month"].min_value, params["month"].max_value), (1, 12))
        self.assertEqual({choice.value for choice in params["category"].choices}, {category.value for category in Category})
        self.assertFalse(self.bot.intents.message_content)
        self.assertFalse(self.bot.intents.members)
        self.assertTrue(self.bot.intents.guilds)

    async def test_admin_commands_enforce_manage_guild_at_runtime(self):
        for name in ("daily", "daily-status", "daily-off"):
            command = self.bot.tree.get_command(name)
            self.assertTrue(command.default_permissions.manage_guild)
            self.assertTrue(command.guild_only)
            self.assertTrue(command.checks)
            request = interaction()
            for check in command.checks:
                with self.assertRaises(app_commands.MissingPermissions):
                    await maybe_coroutine(check, request)
                request.permissions.manage_guild = True
                self.assertTrue(await maybe_coroutine(check, request))

    async def test_invalid_dates_reply_before_upstream_request(self):
        self.bot.history = SimpleNamespace(get=AsyncMock())
        command = self.bot.tree.get_command("today")
        for month, day in ((10, None), (None, 4), (4, 31)):
            request = interaction()
            await command.callback(request, month=month, day=day)
            request.response.send_message.assert_awaited_once()
            self.assertTrue(request.response.send_message.await_args.kwargs["ephemeral"])
            request.response.defer.assert_not_awaited()
        self.bot.history.get.assert_not_awaited()

    async def test_today_uses_configured_local_date_and_source(self):
        result = HistoryResult(10, 5, Category.EVENTS, (HistoryItem("1957年", "資料"),), source_url(10, 5))
        self.bot.history = SimpleNamespace(get=AsyncMock(return_value=result))
        request = interaction()
        with patch("history_bot.bot.datetime") as clock:
            clock.now.return_value = datetime(2026, 10, 5, 0, 1, tzinfo=timezone.utc)
            await self.bot.tree.get_command("today").callback(request)
            self.assertEqual(str(clock.now.call_args.args[0]), "Asia/Taipei")
        self.bot.history.get.assert_awaited_once_with(10, 5, Category.EVENTS)
        request.response.defer.assert_awaited_once()
        embed = request.edit_original_response.await_args.kwargs["embed"]
        self.assertEqual(embed.url, result.source_url)

    async def test_leap_day_lookup_is_supported(self):
        result = HistoryResult(2, 29, Category.BIRTHS, (), source_url(2, 29))
        self.bot.history = SimpleNamespace(get=AsyncMock(return_value=result))
        request = interaction()
        await self.bot.tree.get_command("today").callback(request, month=2, day=29, category="births")
        self.bot.history.get.assert_awaited_once_with(2, 29, Category.BIRTHS)

    async def test_friendly_upstream_error_finishes_deferred_response(self):
        request = interaction()
        request.response.is_done.return_value = True
        error = app_commands.CommandInvokeError(self.bot.tree.get_command("today"), HistoryError("查詢維基百科逾時，請稍後再試。"))
        await self.bot.on_command_error(request, error)
        request.edit_original_response.assert_awaited_once_with(content="查詢維基百科逾時，請稍後再試。", embed=None)

    async def test_channel_permission_requirements(self):
        channel = SimpleNamespace(permissions_for=Mock(return_value=discord.Permissions.none()))
        member = object()
        permissions = channel.permissions_for.return_value
        for name in ("view_channel", "send_messages", "embed_links"):
            self.assertFalse(self.bot.can_post(channel, member))
            setattr(permissions, name, True)
        self.assertTrue(self.bot.can_post(channel, member))


class EmbedTests(unittest.TestCase):
    def test_long_source_entries_fit_discord_and_neutralize_mentions(self):
        items = tuple(HistoryItem("2000年", "@everyone <@123456789012345678> **" + "很長的內容" * 200) for _ in range(10))
        embed = build_embed(HistoryResult(10, 4, Category.EVENTS, items, source_url(10, 4)), count=10)
        self.assertLessEqual(len(embed.description), 4096)
        self.assertLessEqual(len(embed), 6000)
        self.assertNotIn("@everyone", embed.description)
        self.assertNotIn("<@123456789012345678>", embed.description)
        self.assertIn("…", embed.description)
        self.assertIn("CC BY-SA", embed.footer.text)


if __name__ == "__main__":
    unittest.main()
