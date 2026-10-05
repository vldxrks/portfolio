from __future__ import annotations

from apps.achievements.models import Achievement, UserAchievement
from apps.notifications.models import Notification
from apps.tracking.models import HabitCompletion

DEFAULT_ACHIEVEMENTS = [
    ("first-step", "First Step", "Completed your first habit", "🌱", "total", 1),
    ("consistency", "Consistency", "Completed 50 habits", "💪", "total", 50),
    ("master", "Master", "Completed 500 habits", "🏆", "total", 500),
    ("streak-7", "7 Day Streak", "Maintained a 7 day streak", "🔥", "streak", 7),
    ("streak-30", "30 Day Streak", "Maintained a 30 day streak", "🔥", "streak", 30),
]


def ensure_default_achievements() -> None:
    for code, title, desc, icon, kind, threshold in DEFAULT_ACHIEVEMENTS:
        Achievement.objects.get_or_create(
            code=code,
            defaults={"title": title, "description": desc, "icon": icon, "kind": kind, "threshold": threshold},
        )


def award_achievements(user) -> list[Achievement]:
    from apps.habits.services.streak_service import calculate_current_streak

    ensure_default_achievements()
    total = HabitCompletion.objects.filter(habit__user=user, value__gte=models_target()).count()
    best_streak = max(
        (calculate_current_streak(h, user.local_today()) for h in user.habits.filter(is_active=True)),
        default=0,
    )
    earned_ids = set(UserAchievement.objects.filter(user=user).values_list("achievement_id", flat=True))
    new = []
    for ach in Achievement.objects.exclude(id__in=earned_ids):
        metric = total if ach.kind == Achievement.Kind.TOTAL else best_streak
        if metric >= ach.threshold:
            UserAchievement.objects.create(user=user, achievement=ach)
            Notification.objects.create(
                user=user,
                type=Notification.Type.ACHIEVEMENT,
                title=f"Achievement unlocked: {ach.title}",
                message=ach.description,
            )
            new.append(ach)
    return new


def models_target():
    from django.db.models import F

    return F("habit__target_value")
