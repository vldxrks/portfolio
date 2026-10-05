import random
from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand

from apps.achievements.services import award_achievements
from apps.habits.models import Habit
from apps.notifications.models import Notification
from apps.tracking.models import HabitCompletion
from apps.users.models import User

DEMO = [
    ("Morning Run", "fitness", "#16a34a", 1, ""),
    ("Read", "learning", "#2563eb", 30, "pages"),
    ("Drink Water", "health", "#0891b2", 2, "liters"),
    ("Meditation", "mindfulness", "#9333ea", 10, "minutes"),
]


class Command(BaseCommand):
    help = "Create demo user (demo@example.com / DemoPassword123!) with history. Never runs automatically."

    def handle(self, *args, **opts):
        random.seed(7)
        user, _ = User.objects.get_or_create(
            username="demo", defaults={"email": "demo@example.com", "first_name": "Alex", "timezone": "Europe/Kyiv"}
        )
        user.set_password("DemoPassword123!")
        user.save()
        today = user.local_today()
        for name, cat, color, target, unit in DEMO:
            habit, _ = Habit.objects.get_or_create(
                user=user,
                name=name,
                defaults={
                    "category": cat,
                    "color": color,
                    "target_value": Decimal(target),
                    "unit": unit,
                    "start_date": today - timedelta(days=60),
                },
            )
            for i in range(60):
                if i < 12 or random.random() < 0.8:
                    HabitCompletion.objects.get_or_create(
                        habit=habit, date=today - timedelta(days=i), defaults={"value": Decimal(target)}
                    )
        award_achievements(user)
        Notification.objects.get_or_create(user=user, title="Welcome to HabitFlow", defaults={"message": "Demo data loaded."})
        self.stdout.write(self.style.SUCCESS("Demo user ready: demo@example.com / DemoPassword123!"))
