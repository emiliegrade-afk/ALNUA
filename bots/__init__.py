from bots.analytics_bot import AnalyticsBot
from bots.discord_bot import DiscordBot, run_discord_bot
from bots.publisher_bot import PublisherBot
from bots.reviews_bot import ReviewsBot
from bots.sav_bot import SAVBot
from bots.watchdog_bot import WatchdogBot

__all__ = [
    "DiscordBot",
    "run_discord_bot",
    "TelegramBot",
    "get_telegram_bot",
    "run_telegram_bot",
    "PublisherBot",
    "ReviewsBot",
    "AnalyticsBot",
    "SAVBot",
    "WatchdogBot",
]


def __getattr__(name: str):
    if name in ("TelegramBot", "get_telegram_bot", "run_telegram_bot"):
        from bots.telegram_bot import TelegramBot, get_telegram_bot, run_telegram_bot

        return {
            "TelegramBot": TelegramBot,
            "get_telegram_bot": get_telegram_bot,
            "run_telegram_bot": run_telegram_bot,
        }[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
