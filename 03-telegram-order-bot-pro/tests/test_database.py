import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ.setdefault("BOT_TOKEN", "test:token")
os.environ.setdefault("ADMIN_IDS", "111")
os.environ["DB_PATH"] = "test_orders.db"

import pytest

import database as db


@pytest.fixture(autouse=True)
def fresh_db():
    if os.path.exists("test_orders.db"):
        os.remove("test_orders.db")
    db.init_db()
    yield
    if os.path.exists("test_orders.db"):
        os.remove("test_orders.db")


def test_add_and_get_order():
    oid = db.add_order(1, "vlad", "bot", "$150 - $300", "About a week", "Need a simple bot")
    order = db.get_order(oid)
    assert order.service == "bot"
    assert order.status == "new"


def test_user_orders_and_status_update():
    oid = db.add_order(1, "vlad", "website", "$300 - $500", "1-3 days (urgent)", "Landing page")
    db.update_status(oid, "in_progress")
    orders = db.get_user_orders(1)
    assert orders[0].status == "in_progress"


def test_pagination():
    for i in range(7):
        db.add_order(1, "vlad", "scraper", "$50 - $150", "Flexible", f"Task {i}")
    page0, total = db.get_orders_page(None, page=0, page_size=5)
    page1, _ = db.get_orders_page(None, page=1, page_size=5)
    assert total == 7
    assert len(page0) == 5
    assert len(page1) == 2


def test_stats():
    db.upsert_user(1, "vlad")
    db.upsert_user(2, "anna")
    db.add_order(1, "vlad", "bot", "$50 - $150", "Flexible", "x")
    db.add_order(2, "anna", "bot", "$50 - $150", "Flexible", "y")
    s = db.get_stats()
    assert s["total_orders"] == 2
    assert s["total_users"] == 2
    assert s["by_status"]["new"] == 2


def test_export_csv(tmp_path):
    db.add_order(1, "vlad", "bot", "$50 - $150", "Flexible", "x")
    path = tmp_path / "out.csv"
    count = db.export_orders_csv(str(path))
    assert count == 1
    assert path.read_text(encoding="utf-8").startswith("id,user_id")
