from datetime import timedelta
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from rest_framework.test import APIClient

from apps.achievements.models import UserAchievement
from apps.habits.services.habit_service import complete_habit, uncomplete_habit
from apps.tracking.models import HabitCompletion

from .factories import HabitFactory, UserFactory

pytestmark = pytest.mark.django_db


def test_complete_awards_xp_and_first_step():
    h = HabitFactory()
    complete_habit(h)
    h.user.refresh_from_db()
    assert h.user.xp == 10
    assert UserAchievement.objects.filter(user=h.user, achievement__code="first-step").exists()


def test_duplicate_completion_is_idempotent():
    h = HabitFactory()
    complete_habit(h)
    complete_habit(h)
    assert HabitCompletion.objects.filter(habit=h).count() == 1
    h.user.refresh_from_db()
    assert h.user.xp == 10


def test_quantitative_progress_accumulates():
    h = HabitFactory(target_value=Decimal("10000"), unit="steps")
    complete_habit(h, value=Decimal("7500"))
    assert HabitCompletion.objects.get(habit=h).value == 7500
    h.user.refresh_from_db()
    assert h.user.xp == 0
    complete_habit(h, value=Decimal("2500"))
    h.user.refresh_from_db()
    assert h.user.xp == 10


def test_future_and_archived_rejected():
    h = HabitFactory()
    with pytest.raises(ValidationError):
        complete_habit(h, day=h.user.local_today() + timedelta(days=1))
    h.archive()
    with pytest.raises(ValidationError):
        complete_habit(h)


def test_uncomplete():
    h = HabitFactory()
    complete_habit(h)
    uncomplete_habit(h)
    assert not HabitCompletion.objects.filter(habit=h).exists()


def test_api_requires_auth(db):
    assert APIClient().get("/api/v1/habits/").status_code == 401


def test_api_crud_pagination_filter(api, user):
    r = api.post("/api/v1/habits/", {"name": "Read", "category": "learning"}, format="json")
    assert r.status_code == 201
    HabitFactory(user=user, name="Run", category="fitness")
    r = api.get("/api/v1/habits/?category=fitness")
    assert r.json()["count"] == 1 and "results" in r.json()
    assert api.get("/api/v1/habits/?search=read").json()["count"] == 1


def test_api_validation(api):
    r = api.post("/api/v1/habits/", {"name": "x", "start_date": "2026-02-01", "end_date": "2026-01-01"}, format="json")
    assert r.status_code == 400


def test_cannot_access_foreign_habit(api):
    other = HabitFactory(user=UserFactory())
    assert api.get(f"/api/v1/habits/{other.id}/").status_code == 404
    assert api.post(f"/api/v1/habits/{other.id}/complete/").status_code == 404
    assert api.delete(f"/api/v1/habits/{other.id}/").status_code == 404


def test_api_complete_statistics_and_soft_delete(api, user):
    h = HabitFactory(user=user)
    assert api.post(f"/api/v1/habits/{h.id}/complete/", {}, format="json").status_code == 201
    st = api.get(f"/api/v1/habits/{h.id}/statistics/").json()
    assert st["current_streak"] == 1
    assert api.delete(f"/api/v1/habits/{h.id}/").status_code == 204
    h.refresh_from_db()
    assert not h.is_active and HabitCompletion.objects.filter(habit=h).exists()


def test_jwt_flow(user):
    c = APIClient()
    tok = c.post("/api/v1/auth/token/", {"username": user.username, "password": "StrongPass123!"}, format="json")
    assert tok.status_code == 200
    c.credentials(HTTP_AUTHORIZATION=f"Bearer {tok.json()['access']}")
    assert c.get("/api/v1/profile/").status_code == 200


def test_web_register_login_dashboard(client, db):
    r = client.post(
        "/register/",
        {
            "username": "neo",
            "email": "neo@example.com",
            "first_name": "Neo",
            "timezone": "Europe/Kyiv",
            "password1": "Zx9!trongPass",
            "password2": "Zx9!trongPass",
        },
    )
    assert r.status_code == 302
    assert client.get("/dashboard/").status_code == 200


def test_dashboard_requires_login_and_health(client, db):
    assert client.get("/dashboard/").status_code == 302
    assert client.get("/health/").json()["database"] == "ok"


def test_foreign_habit_page_404(client, user):
    client.force_login(user)
    other = HabitFactory(user=UserFactory())
    assert client.get(f"/habits/{other.id}/").status_code == 404
