import pytest
from rest_framework.test import APIClient

from .factories import UserFactory


@pytest.fixture
def user(db):
    return UserFactory()


@pytest.fixture
def api(user):
    c = APIClient()
    c.force_authenticate(user)
    return c
