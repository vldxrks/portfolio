from datetime import time
from unittest.mock import patch
from zoneinfo import ZoneInfo

import pytest
from django.core.management import call_command
from django.utils import timezone

from apps.notifications.models import Notification
from apps.notifications.tasks import cleanup_old_notifications, send_due_reminders

from .factories import HabitFactory

pytestmark = pytest.mark.django_db


def test_habit_pages_flow(client, user):
    client.force_login(user)
    r = client.post(
        "/habits/create/",
        {
            "name": "Read",
            "category": "learning",
            "color": "#2563eb",
            "icon": "book",
            "frequency": "daily",
            "target_count": 1,
            "target_value": "30",
            "unit": "pages",
            "start_date": "2026-01-01",
        },
    )
    assert r.status_code == 302
    habit = user.habits.get()
    assert client.get("/habits/").status_code == 200
    assert client.get("/habits/?q=read").status_code == 200
    assert client.get(f"/habits/{habit.id}/").status_code == 200
    assert client.get(f"/habits/{habit.id}/edit/").status_code == 200
    assert client.post(f"/habits/{habit.id}/complete/").status_code == 302
    for url in ("/dashboard/", "/analytics/", "/achievements/", "/notifications/", "/export/completions.csv"):
        assert client.get(url).status_code == 200
    assert client.post("/notifications/").status_code == 302
    client.post(f"/habits/{habit.id}/archive/")
    habit.refresh_from_db()
    assert not habit.is_active


def test_invalid_form_shows_errors(client, user):
    client.force_login(user)
    r = client.post(
        "/habits/create/",
        {
            "name": "x",
            "frequency": "weekdays",
            "target_value": "1",
            "category": "other",
            "color": "#000000",
            "icon": "x",
            "target_count": 1,
            "start_date": "2026-01-01",
        },
    )
    assert r.status_code == 200 and not user.habits.exists()


def test_seed_demo_and_api_summary(client):
    call_command("seed_demo")
    assert client.login(username="demo@example.com", password="DemoPassword123!")
    assert client.get("/dashboard/").status_code == 200


def test_reminder_task_and_cleanup(user):
    now = timezone.now().astimezone(ZoneInfo(user.timezone))
    HabitFactory(user=user, reminder_enabled=True, reminder_time=time(now.hour, now.minute))
    assert send_due_reminders() == 1
    Notification.objects.update(is_read=True)
    with patch("apps.notifications.tasks.timezone.now", return_value=timezone.now() + timezone.timedelta(days=90)):
        assert cleanup_old_notifications() == 1


def test_landing_and_static_theme(client, db):
    r = client.get("/")
    assert r.status_code == 200 and b"apple.css" in r.content


def test_auth_pages_render(client, db):
    for url in ("/login/", "/register/"):
        r = client.get(url)
        assert r.status_code == 200 and b'id="bg"' in r.content and b"auth-card" in r.content
    bad = client.post("/login/", {"username": "nobody", "password": "x"})
    assert bad.status_code == 200 and b"Incorrect" in bad.content
