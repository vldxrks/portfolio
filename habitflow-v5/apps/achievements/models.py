from django.conf import settings
from django.db import models


class Achievement(models.Model):
    class Kind(models.TextChoices):
        TOTAL = "total", "Total completions"
        STREAK = "streak", "Streak length"

    code = models.SlugField(unique=True)
    title = models.CharField(max_length=80)
    description = models.CharField(max_length=200)
    icon = models.CharField(max_length=8, default="🏆")
    kind = models.CharField(max_length=10, choices=Kind.choices)
    threshold = models.PositiveIntegerField()

    class Meta:
        ordering = ["kind", "threshold"]

    def __str__(self) -> str:
        return self.title


class UserAchievement(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="achievements")
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE)
    earned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "achievement"], name="unique_user_achievement")]

    def __str__(self) -> str:
        return f"{self.user_id}:{self.achievement_id}"
