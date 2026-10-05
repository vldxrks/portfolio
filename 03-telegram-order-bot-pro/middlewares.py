"""Simple anti-spam throttling middleware: ignores a user's messages/clicks that
arrive faster than config.THROTTLE_SECONDS after their previous one."""
import time
from collections import defaultdict
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from config import config


class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self) -> None:
        self._last_seen: dict[int, float] = defaultdict(float)

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = data.get("event_from_user")
        if user is not None:
            now = time.monotonic()
            if now - self._last_seen[user.id] < config.THROTTLE_SECONDS:
                return  # silently drop, too fast
            self._last_seen[user.id] = now
        return await handler(event, data)
