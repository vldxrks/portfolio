from decimal import Decimal

from django.db import models
from django.utils import timezone


class HabitCompletion(models.Model):
    """One row per habit per local day; `value` accumulates progress toward habit.target_value."""

    habit = models.ForeignKey("habits.Habit", on_delete=models.CASCADE, related_name="completions")
    date = models.DateField()
    value = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("1"))
    note = models.CharField(max_length=500, blank=True)
    completed_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-date"]
        constraints = [models.UniqueConstraint(fields=["habit", "date"], name="unique_completion_per_day")]
        indexes = [models.Index(fields=["habit", "-date"])]

    def __str__(self) -> str:
        return f"{self.habit_id} @ {self.date}"

    @property
    def is_done(self) -> bool:
        return self.value >= self.habit.target_value
