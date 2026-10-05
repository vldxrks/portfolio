"""SQLite data layer: users, orders, simple stats. No ORM, raw sqlite3 for transparency."""
import sqlite3
from contextlib import closing
from dataclasses import dataclass
from datetime import datetime, timezone

from config import config

SERVICES = {
    "website": "Website",
    "bot": "Telegram bot",
    "automation": "Automation script",
    "scraper": "Web scraper",
    "other": "Other",
}

BUDGETS = {
    "50-150": "$50 - $150",
    "150-300": "$150 - $300",
    "300-500": "$300 - $500",
    "500+": "$500+",
}

DEADLINES = {
    "urgent": "1-3 days (urgent)",
    "standard": "About a week",
    "flexible": "2+ weeks, flexible",
}

STATUSES = {
    "new": "🆕 New",
    "in_progress": "⏳ In progress",
    "done": "✅ Done",
    "cancelled": "❌ Cancelled",
}


@dataclass
class Order:
    id: int
    user_id: int
    username: str | None
    service: str
    budget: str
    deadline: str
    description: str
    status: str
    created_at: str


def init_db() -> None:
    with closing(sqlite3.connect(config.DB_PATH)) as conn, conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_seen TEXT DEFAULT CURRENT_TIMESTAMP
            )"""
        )
        conn.execute(
            """CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                username TEXT,
                service TEXT NOT NULL,
                budget TEXT NOT NULL,
                deadline TEXT NOT NULL,
                description TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'new',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )"""
        )


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def upsert_user(user_id: int, username: str | None) -> None:
    with closing(_connect()) as conn, conn:
        conn.execute(
            "INSERT INTO users (user_id, username) VALUES (?, ?) "
            "ON CONFLICT(user_id) DO UPDATE SET username = excluded.username",
            (user_id, username),
        )


def all_user_ids() -> list[int]:
    with closing(_connect()) as conn:
        return [row["user_id"] for row in conn.execute("SELECT user_id FROM users")]


def add_order(user_id: int, username: str | None, service: str, budget: str, deadline: str, description: str) -> int:
    with closing(_connect()) as conn, conn:
        cur = conn.execute(
            "INSERT INTO orders (user_id, username, service, budget, deadline, description) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, username, service, budget, deadline, description),
        )
        return cur.lastrowid


def get_order(order_id: int) -> Order | None:
    with closing(_connect()) as conn:
        row = conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
        return Order(**dict(row)) if row else None


def get_user_orders(user_id: int, limit: int = 10) -> list[Order]:
    with closing(_connect()) as conn:
        rows = conn.execute(
            "SELECT * FROM orders WHERE user_id = ? ORDER BY id DESC LIMIT ?", (user_id, limit)
        ).fetchall()
        return [Order(**dict(r)) for r in rows]


def get_orders_page(status: str | None, page: int, page_size: int = 5) -> tuple[list[Order], int]:
    """Returns (orders for this page, total count for this filter)."""
    with closing(_connect()) as conn:
        if status:
            total = conn.execute("SELECT COUNT(*) c FROM orders WHERE status = ?", (status,)).fetchone()["c"]
            rows = conn.execute(
                "SELECT * FROM orders WHERE status = ? ORDER BY id DESC LIMIT ? OFFSET ?",
                (status, page_size, page * page_size),
            ).fetchall()
        else:
            total = conn.execute("SELECT COUNT(*) c FROM orders").fetchone()["c"]
            rows = conn.execute(
                "SELECT * FROM orders ORDER BY id DESC LIMIT ? OFFSET ?", (page_size, page * page_size)
            ).fetchall()
        return [Order(**dict(r)) for r in rows], total


def update_status(order_id: int, status: str) -> None:
    with closing(_connect()) as conn, conn:
        conn.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))


def get_stats() -> dict:
    with closing(_connect()) as conn:
        total_orders = conn.execute("SELECT COUNT(*) c FROM orders").fetchone()["c"]
        total_users = conn.execute("SELECT COUNT(*) c FROM users").fetchone()["c"]
        by_status = dict(
            conn.execute("SELECT status, COUNT(*) c FROM orders GROUP BY status").fetchall()
        )
        by_service = conn.execute(
            "SELECT service, COUNT(*) c FROM orders GROUP BY service ORDER BY c DESC"
        ).fetchall()
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        today_orders = conn.execute(
            "SELECT COUNT(*) c FROM orders WHERE date(created_at) = ?", (today,)
        ).fetchone()["c"]
    return {
        "total_orders": total_orders,
        "total_users": total_users,
        "by_status": by_status,
        "by_service": by_service,
        "today_orders": today_orders,
    }


def export_orders_csv(path: str) -> int:
    import csv

    with closing(_connect()) as conn:
        rows = conn.execute("SELECT * FROM orders ORDER BY id").fetchall()
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "user_id", "username", "service", "budget", "deadline", "description", "status", "created_at"])
        for r in rows:
            writer.writerow(list(r))
    return len(rows)
