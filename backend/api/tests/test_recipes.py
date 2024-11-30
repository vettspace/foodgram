import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from recipes.models import Recipe, Tag


@pytest.mark.django_db
class TestRecipes:
    def test_recipe_list(self, client):
        url = reverse('api:recipe-list')
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_recipe_create(self, authenticated_client, user):
        url = reverse('api:recipe-list')
        tag = Tag.objects.create(name='Test tag', slug='test-tag')
        data = {
            'name': 'Test recipe',
            'text': 'Test description',
            'cooking_time': 30,
            'tags': [tag.id],
            'ingredients': [{'id': 1, 'amount': 100}],
            'image': 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+P+/HgAFhAJ/wlseKgAAAABJRU5ErkJggg==',
        }
        response = authenticated_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
