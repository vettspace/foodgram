from api.permissions import IsAdminOrReadOnly
from django.shortcuts import get_object_or_404
from recipes.models import Recipe, RecipeIngredient
from rest_framework.permissions import AllowAny


class RecipeAccessMixin:
    """
    Миксин для получения объекта рецепта и проверки прав доступа.
    """

    serializer_class = None
    permission_classes = (AllowAny,)

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
    Миксин для установки прав доступа и отключения пагинации.
    """

    permission_classes = (IsAdminOrReadOnly,)
    pagination_class = None


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
