"""Loads and validates configuration from environment variables (.env)."""
import os

from dotenv import load_dotenv

load_dotenv()


def _parse_admin_ids(raw: str) -> set[int]:
    return {int(x.strip()) for x in raw.split(",") if x.strip()}


class Config:
    BOT_TOKEN: str = os.environ["BOT_TOKEN"]
    ADMIN_IDS: set[int] = _parse_admin_ids(os.environ["ADMIN_IDS"])
    DB_PATH: str = os.getenv("DB_PATH", "orders.db")
    THROTTLE_SECONDS: float = float(os.getenv("THROTTLE_SECONDS", "0.7"))


config = Config()
