from __future__ import annotations

from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import F

from apps.achievements.services import award_achievements
from apps.habits.models import Habit
from apps.tracking.models import HabitCompletion

from .streak_service import calculate_current_streak

XP_PER_COMPLETION = 10
STREAK_BONUS = {7: 50, 30: 200}


@transaction.atomic
def complete_habit(habit: Habit, day: date | None = None, value: Decimal | None = None, note: str = "") -> HabitCompletion:
    """Add progress for `day` (user's local today by default). Idempotent once the target is reached."""
    if not habit.is_active:
        raise ValidationError("Archived habits cannot be completed.")
    user = habit.user
    day = day or user.local_today()
    if day > user.local_today():
        raise ValidationError("Cannot complete a habit in the future.")
    if not habit.is_scheduled_on(day):
        raise ValidationError("Habit is not scheduled on this date.")
    value = Decimal(value) if value is not None else habit.target_value
    if value <= 0:
        raise ValidationError("Value must be positive.")

    completion, created = HabitCompletion.objects.select_for_update().get_or_create(
        habit=habit, date=day, defaults={"value": value, "note": note}
    )
    was_done = (not created) and completion.value >= habit.target_value
    if not created:
        if was_done:
            return completion
        completion.value += value
        if note:
            completion.note = note
        completion.save(update_fields=["value", "note"])

    if completion.value >= habit.target_value:
        _grant_xp(habit, day)
        award_achievements(user)
    return completion


def _grant_xp(habit: Habit, day: date) -> None:
    user = habit.user
    xp = XP_PER_COMPLETION
    streak = calculate_current_streak(habit, day)
    xp += STREAK_BONUS.get(streak, 0)
    type(user).objects.filter(pk=user.pk).update(xp=F("xp") + xp)
    user.refresh_from_db(fields=["xp"])


@transaction.atomic
def uncomplete_habit(habit: Habit, day: date | None = None) -> None:
    day = day or habit.user.local_today()
    HabitCompletion.objects.filter(habit=habit, date=day).delete()
