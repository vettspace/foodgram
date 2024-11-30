"""Для фикстур"""

import pytest
from rest_framework.test import APIClient
from users.models import User


@pytest.fixture
def user():
    return User.objects.create_user(
        username='testuser',
        email='test@test.com',
        password='testpass123',
        first_name='Test',
        last_name='User',
    )


@pytest.fixture
def authenticated_client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client
