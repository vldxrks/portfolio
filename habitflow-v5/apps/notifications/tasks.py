import logging
from datetime import timedelta
from zoneinfo import ZoneInfo

from celery import shared_task
from django.utils import timezone

from apps.habits.models import Habit
from apps.tracking.models import HabitCompletion

from .models import Notification

logger = logging.getLogger(__name__)


@shared_task
def send_due_reminders() -> int:
    """Create a reminder for every habit whose local reminder minute is now and which isn't done today."""
    now = timezone.now()
    sent = 0
    habits = Habit.objects.filter(is_active=True, reminder_enabled=True).select_related("user")
    for habit in habits:
        local = now.astimezone(ZoneInfo(habit.user.timezone))
        t = habit.reminder_time
        if (t.hour, t.minute) != (local.hour, local.minute) or not habit.is_scheduled_on(local.date()):
            continue
        if HabitCompletion.objects.filter(habit=habit, date=local.date(), value__gte=habit.target_value).exists():
            continue
        Notification.objects.create(
            user=habit.user,
            type=Notification.Type.REMINDER,
            title=f"Time for: {habit.name}",
            message="Keep your streak going.",
        )
        sent += 1
    logger.info("reminders sent: %s", sent)
    return sent


@shared_task
def cleanup_old_notifications(days: int = 60) -> int:
    deleted, _ = Notification.objects.filter(is_read=True, created_at__lt=timezone.now() - timedelta(days=days)).delete()
    return deleted
