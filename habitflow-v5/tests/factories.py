from datetime import date, timedelta

import factory

from apps.habits.models import Habit
from apps.tracking.models import HabitCompletion
from apps.users.models import User


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda o: f"{o.username}@example.com")
    password = factory.PostGenerationMethodCall("set_password", "StrongPass123!")
    timezone = "Europe/Kyiv"


class HabitFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Habit

    user = factory.SubFactory(UserFactory)
    name = factory.Sequence(lambda n: f"Habit {n}")
    start_date = factory.LazyFunction(lambda: date.today() - timedelta(days=400))


class HabitCompletionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = HabitCompletion

    habit = factory.SubFactory(HabitFactory)
    date = factory.LazyFunction(date.today)
