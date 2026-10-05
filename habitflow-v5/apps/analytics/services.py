from __future__ import annotations

from datetime import date, timedelta

from django.db.models import Count

from apps.habits.models import Habit
from apps.habits.services.streak_service import calculate_completion_rate
from apps.tracking.models import HabitCompletion


def daily_completions(user, today: date, days: int = 30) -> list[dict]:
    start = today - timedelta(days=days - 1)
    rows = (
        HabitCompletion.objects.filter(habit__user=user, date__gte=start)
        .filter(value__gte=models_target())
        .values("date")
        .annotate(n=Count("id"))
    )
    by_day = {r["date"]: r["n"] for r in rows}
    return [
        {"date": (start + timedelta(days=i)).isoformat(), "count": by_day.get(start + timedelta(days=i), 0)} for i in range(days)
    ]


def models_target():
    from django.db.models import F

    return F("habit__target_value")


def habit_performance(user, today: date) -> list[dict]:
    habits = Habit.objects.filter(user=user, is_active=True)
    data = [{"id": h.id, "name": h.name, "rate": calculate_completion_rate(h, today)} for h in habits]
    return sorted(data, key=lambda x: -x["rate"])


def summary(user, today: date) -> dict:
    perf = habit_performance(user, today)
    return {
        "daily_30": daily_completions(user, today, 30),
        "performance": perf,
        "best": perf[:3],
        "weak": list(reversed(perf[-3:])),
    }
