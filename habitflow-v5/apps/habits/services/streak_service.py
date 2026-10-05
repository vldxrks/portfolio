from __future__ import annotations

from datetime import date, timedelta

from apps.habits.models import Habit
from apps.tracking.models import HabitCompletion


def done_dates(habit: Habit) -> set[date]:
    rows = HabitCompletion.objects.filter(habit=habit, value__gte=habit.target_value)
    return set(rows.values_list("date", flat=True))


def _week_start(d: date) -> date:
    return d - timedelta(days=d.weekday())


def _weekly_runs(done: set[date], target: int) -> list[date]:
    counts: dict[date, int] = {}
    for d in done:
        counts[_week_start(d)] = counts.get(_week_start(d), 0) + 1
    return sorted(w for w, c in counts.items() if c >= target)


def _longest_run(units: list[date], step: timedelta) -> int:
    best = run = 0
    prev = None
    for u in units:
        run = run + 1 if prev is not None and u - prev == step else 1
        best = max(best, run)
        prev = u
    return best


def calculate_current_streak(habit: Habit, today: date, done: set[date] | None = None) -> int:
    """Consecutive scheduled days (or weeks for times_per_week) completed, ending today or the last
    scheduled period. A not-yet-completed today does not break the streak."""
    done = done if done is not None else done_dates(habit)
    if habit.frequency == Habit.Frequency.TIMES_PER_WEEK:
        weeks = set(_weekly_runs(done, habit.target_count))
        cursor = _week_start(today)
        if cursor not in weeks:
            cursor -= timedelta(weeks=1)
        streak = 0
        while cursor in weeks:
            streak += 1
            cursor -= timedelta(weeks=1)
        return streak

    streak = 0
    cursor = today
    if cursor not in done:
        cursor -= timedelta(days=1)
    while cursor >= habit.start_date:
        if habit.is_scheduled_on(cursor):
            if cursor not in done:
                break
            streak += 1
        cursor -= timedelta(days=1)
    return streak


def calculate_longest_streak(habit: Habit, done: set[date] | None = None) -> int:
    done = done if done is not None else done_dates(habit)
    if not done:
        return 0
    if habit.frequency == Habit.Frequency.TIMES_PER_WEEK:
        return _longest_run(_weekly_runs(done, habit.target_count), timedelta(weeks=1))
    best = run = 0
    cursor, last = min(done), max(done)
    while cursor <= last:
        if habit.is_scheduled_on(cursor):
            run = run + 1 if cursor in done else 0
            best = max(best, run)
        cursor += timedelta(days=1)
    return best


def calculate_completion_rate(habit: Habit, today: date, days: int = 30) -> float:
    start = max(habit.start_date, today - timedelta(days=days - 1))
    scheduled = [start + timedelta(days=i) for i in range((today - start).days + 1)]
    scheduled = [d for d in scheduled if habit.is_scheduled_on(d)]
    if not scheduled:
        return 0.0
    done = done_dates(habit)
    return round(100 * sum(d in done for d in scheduled) / len(scheduled), 1)
