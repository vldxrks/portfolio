from zoneinfo import ZoneInfo, available_timezones

from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


def validate_timezone(value: str) -> None:
    if value not in available_timezones():
        raise ValidationError("Unknown timezone: %(value)s", params={"value": value})


class User(AbstractUser):
    email = models.EmailField(unique=True)
    avatar = models.ImageField(upload_to="avatars/", blank=True)
    timezone = models.CharField(max_length=64, default="Europe/Kyiv", validators=[validate_timezone])
    xp = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def level(self) -> int:
        return self.xp // 100 + 1

    def local_today(self):
        return timezone.now().astimezone(ZoneInfo(self.timezone)).date()
