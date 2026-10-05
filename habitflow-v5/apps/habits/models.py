from datetime import date

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class Habit(models.Model):
    class Category(models.TextChoices):
        HEALTH = "health", "Health"
        FITNESS = "fitness", "Fitness"
        LEARNING = "learning", "Learning"
        PRODUCTIVITY = "productivity", "Productivity"
        FINANCE = "finance", "Finance"
        SOCIAL = "social", "Social"
        MINDFULNESS = "mindfulness", "Mindfulness"
        OTHER = "other", "Other"

    class Frequency(models.TextChoices):
        DAILY = "daily", "Every day"
        WEEKDAYS = "weekdays", "Specific weekdays"
        TIMES_PER_WEEK = "times_per_week", "N times per week"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="habits")
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=20, choices=Category.choices, default=Category.OTHER)
    color = models.CharField(max_length=7, default="#4f46e5")
    icon = models.CharField(max_length=40, default="check-circle")
    frequency = models.CharField(max_length=20, choices=Frequency.choices, default=Frequency.DAILY)
    weekdays = models.JSONField(default=list, blank=True, help_text="0=Mon..6=Sun, used with 'weekdays'")
    target_count = models.PositiveSmallIntegerField(default=1, help_text="Times per week (times_per_week)")
    target_value = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    unit = models.CharField(max_length=30, blank=True)
    start_date = models.DateField(default=date.today)
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    archived_at = models.DateTimeField(null=True, blank=True)
    reminder_enabled = models.BooleanField(default=False)
    reminder_time = models.TimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["user", "is_active"]),
            models.Index(fields=["user", "category"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(end_date__isnull=True) | models.Q(end_date__gte=models.F("start_date")),
                name="habit_end_after_start",
            ),
            models.CheckConstraint(condition=models.Q(target_value__gt=0), name="habit_target_value_positive"),
        ]

    def __str__(self) -> str:
        return self.name

    def clean(self) -> None:
        if self.end_date and self.end_date < self.start_date:
            raise ValidationError({"end_date": "End date must not be before start date."})
        if self.target_value is not None and self.target_value <= 0:
            raise ValidationError({"target_value": "Target must be positive."})
        if self.frequency == self.Frequency.WEEKDAYS:
            if not self.weekdays or any(d not in range(7) for d in self.weekdays):
                raise ValidationError({"weekdays": "Choose at least one weekday (0-6)."})
        if self.frequency == self.Frequency.TIMES_PER_WEEK and not 1 <= self.target_count <= 7:
            raise ValidationError({"target_count": "Must be between 1 and 7."})
        if self.reminder_enabled and not self.reminder_time:
            raise ValidationError({"reminder_time": "Reminder time is required when reminders are on."})

    def is_scheduled_on(self, day: date) -> bool:
        if day < self.start_date or (self.end_date and day > self.end_date):
            return False
        if self.frequency == self.Frequency.WEEKDAYS:
            return day.weekday() in self.weekdays
        return True

    def archive(self) -> None:
        self.is_active = False
        self.archived_at = timezone.now()
        self.save(update_fields=["is_active", "archived_at", "updated_at"])

    def restore(self) -> None:
        self.is_active = True
        self.archived_at = None
        self.save(update_fields=["is_active", "archived_at", "updated_at"])
