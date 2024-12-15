from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response

from recipes.models import Recipe, RecipeIngredient


class RecipeAccessMixin:
    """
    Миксин для получения объекта рецепта и проверки прав доступа.
    """

    serializer_class = None
    permission_classes = (AllowAny,)
    http_method_names = ['get', 'options', 'head']

    def get_recipe(self):
        """
        Получает объект рецепта по идентификатору из URL.
        """
        recipe_id = self.kwargs['recipe_id']
        recipe = get_object_or_404(Recipe, id=recipe_id)
        self.check_object_permissions(self.request, recipe)
        return recipe


class AdminOrReadOnlyMixin:
    """
    Миксин для предоставления доступа только администраторам
    или в режиме только для чтения.
    """

    def get_permissions(self):
        """
        Устанавливает разрешения в зависимости от действия.
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return [AllowAny()]

    def handle_no_permission(self):
        """
        Обрабатывает случай, когда пользователь не имеет прав доступа.
        """
        return Response(
            {"detail": "Method not allowed."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )


class SubscriptionMixin:
    """
    Миксин для проверки подписки пользователя.
    """

    def get_is_subscribed(self, obj):
        """
        Проверяет, подписан ли текущий пользователь на автора.
        """
        user = self.context['request'].user
        return (
            user.is_authenticated and user.follower.filter(author=obj).exists()
        )


class PasswordValidationMixin:
    """
    Миксин для валидации пароля.
    """

    def validate_password(self, password):
        """
        Проверяет пароль на соответствие требованиям безопасности.
        """
        from django.contrib.auth.password_validation import validate_password

        validate_password(password)
        return password


class IngredientCreationMixin:
    """
    Миксин для создания ингредиентов в рецепте.
    """

    def create_ingredients(self, ingredients, recipe):
        """
        Создает ингредиенты для рецепта.
        """
        for ingredient in ingredients:
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient_id=ingredient.get('id'),
                amount=ingredient.get('amount'),
            )
