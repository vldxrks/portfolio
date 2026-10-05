from django.conf import settings
from django.db import models


class Notification(models.Model):
    class Type(models.TextChoices):
        REMINDER = "reminder", "Reminder"
        ACHIEVEMENT = "achievement", "Achievement"
        SYSTEM = "system", "System"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    type = models.CharField(max_length=20, choices=Type.choices, default=Type.SYSTEM)
    title = models.CharField(max_length=120)
    message = models.TextField(blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "is_read"])]

    def __str__(self) -> str:
        return self.title
