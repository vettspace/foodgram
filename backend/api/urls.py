from api.views import (CustomUserViewSet, FavoriteRecipeView,
                       IngredientViewSet, RecipeViewSet, ShoppingCartView,
                       SubscriptionView, TagViewSet)
from django.urls import include, path
from rest_framework.routers import DefaultRouter

app_name = 'api'

router = DefaultRouter()
router.register('users', CustomUserViewSet, basename='users')
router.register('tags', TagViewSet, basename='tags')
router.register('ingredients', IngredientViewSet, basename='ingredients')
router.register('recipes', RecipeViewSet, basename='recipes')

urlpatterns = [
    # Управление подписками
    path(
        'users/<int:user_id>/subscribe/',
        SubscriptionView.as_view(),
        name='subscribe',
    ),
    # Управление избранными рецептами
    path(
        'recipes/<int:recipe_id>/favorite/',
        FavoriteRecipeView.as_view(),
        name='favorite_recipe',
    ),
    # Управление корзиной покупок
    path(
        'recipes/<int:recipe_id>/shopping_cart/',
        ShoppingCartView.as_view(),
        name='shopping_cart',
    ),
    # Управление аватаром пользователя
    path(
        'users/me/avatar/',
        CustomUserViewSet.as_view(
            {
                'put': 'upload_avatar',
                'delete': 'delete_avatar',
            }
        ),
        name='avatar',
    ),
    # Основные маршруты
    path('', include(router.urls)),
    # Маршруты Djoser
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]
