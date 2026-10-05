from datetime import date, timedelta

import pytest

from apps.habits.models import Habit
from apps.habits.services import streak_service as s

from .factories import HabitCompletionFactory, HabitFactory

pytestmark = pytest.mark.django_db
D = date(2026, 1, 10)


def mark(habit, *days):
    for d in days:
        HabitCompletionFactory(habit=habit, date=d)


def test_three_consecutive_days():
    h = HabitFactory(start_date=date(2026, 1, 1))
    mark(h, date(2026, 1, 1), date(2026, 1, 2), date(2026, 1, 3))
    assert s.calculate_current_streak(h, date(2026, 1, 3)) == 3
    assert s.calculate_longest_streak(h) == 3


def test_gap_resets_current_not_longest():
    h = HabitFactory(start_date=date(2026, 1, 1))
    mark(h, date(2026, 1, 1), date(2026, 1, 2), date(2026, 1, 4))
    assert s.calculate_current_streak(h, date(2026, 1, 4)) == 1
    assert s.calculate_longest_streak(h) == 2


def test_today_not_done_keeps_streak():
    h = HabitFactory(start_date=date(2026, 1, 1))
    mark(h, date(2026, 1, 8), date(2026, 1, 9))
    assert s.calculate_current_streak(h, D) == 2


def test_missed_yesterday_and_today_is_zero():
    h = HabitFactory(start_date=date(2026, 1, 1))
    mark(h, date(2026, 1, 7))
    assert s.calculate_current_streak(h, D) == 0


def test_long_streak():
    h = HabitFactory(start_date=D - timedelta(days=400))
    mark(h, *[D - timedelta(days=i) for i in range(365)])
    assert s.calculate_current_streak(h, D) == 365


def test_weekday_schedule_skips_unscheduled_days():
    # Mon/Wed/Fri habit; Jan 5 2026 is Monday
    h = HabitFactory(frequency=Habit.Frequency.WEEKDAYS, weekdays=[0, 2, 4], start_date=date(2026, 1, 1))
    mark(h, date(2026, 1, 5), date(2026, 1, 7), date(2026, 1, 9))
    assert s.calculate_current_streak(h, date(2026, 1, 9)) == 3


def test_times_per_week_counts_weeks():
    h = HabitFactory(frequency=Habit.Frequency.TIMES_PER_WEEK, target_count=2, start_date=date(2025, 12, 1))
    mark(h, date(2026, 1, 5), date(2026, 1, 6), date(2026, 1, 12), date(2026, 1, 14))
    assert s.calculate_current_streak(h, date(2026, 1, 14)) == 2


def test_partial_quantitative_day_does_not_count():
    h = HabitFactory(target_value=10, start_date=date(2026, 1, 1))
    HabitCompletionFactory(habit=h, date=date(2026, 1, 9), value=7)
    assert s.calculate_current_streak(h, D) == 0
