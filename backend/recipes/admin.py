from django.contrib import admin

from api.constants import EMPTY

from .models import (FavoriteRecipe, Ingredient, Recipe, RecipeIngredient,
                     ShoppingCart, Subscribe, Tag)


class RecipeIngredientAdmin(admin.StackedInline):
    """
    Админ-интерфейс для управления ингредиентами в рецепте.
    """

    model = RecipeIngredient
    autocomplete_fields = ('ingredient',)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """
    Админ-интерфейс для управления рецептами.
    """

    list_display = (
        'id',
        'get_author',
        'name',
        'text',
        'cooking_time',
        'get_tags',
        'get_ingredients',
        'pub_date',
        'get_favorite_count',
    )
    search_fields = (
        'name',
        'cooking_time',
        'author__email',
        'ingredients__name',
    )
    list_filter = (
        'pub_date',
        'tags',
    )
    inlines = (RecipeIngredientAdmin,)
    empty_value_display = EMPTY

    @admin.display(description='E-mail автора')
    def get_author(self, obj):
        """
        Возвращает email автора рецепта.
        """
        return obj.author.email

    @admin.display(description='Тэги')
    def get_tags(self, obj):
        """
        Возвращает список тегов рецепта.
        """
        return ', '.join(tag.name for tag in obj.tags.all())

    @admin.display(description='Ингредиенты')
    def get_ingredients(self, obj):
        """
        Возвращает список ингредиентов рецепта.
        """
        return '\n '.join(
            f'{item["ingredient__name"]} - {item["amount"]} '
            f'{item["ingredient__measurement_unit"]}.'
            for item in obj.recipe.values(
                'ingredient__name',
                'amount',
                'ingredient__measurement_unit',
            )
        )

    @admin.display(description='В избранном')
    def get_favorite_count(self, obj):
        """
        Возвращает количество добавлений рецепта в избранное.
        """
        return obj.favorite_recipe.count()


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """
    Админ-интерфейс для управления тегами.
    """

    list_display = (
        'id',
        'name',
        'color',
        'slug',
    )
    search_fields = (
        'name',
        'slug',
    )
    empty_value_display = EMPTY


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """
    Админ-интерфейс для управления ингредиентами.
    """

    list_display = (
        'id',
        'name',
        'measurement_unit',
    )
    search_fields = (
        'name',
        'measurement_unit',
    )
    empty_value_display = EMPTY


@admin.register(Subscribe)
class SubscribeAdmin(admin.ModelAdmin):
    """
    Админ-интерфейс для управления подписками.
    """

    list_display = (
        'id',
        'user',
        'author',
        'created',
    )
    search_fields = (
        'user__email',
        'author__email',
    )
    empty_value_display = EMPTY


@admin.register(FavoriteRecipe)
class FavoriteRecipeAdmin(admin.ModelAdmin):
    """
    Админ-интерфейс для управления избранными рецептами.
    """

    list_display = ('id', 'user', 'get_recipe', 'get_count')
    empty_value_display = EMPTY

    @admin.display(description='Рецепты')
    def get_recipe(self, obj):
        """
        Возвращает список первых пяти рецептов в избранном.

        :param obj: Объект избранного рецепта
        :return: Список названий рецептов
        """
        return [f'{item["name"]} ' for item in obj.recipe.values('name')[:5]]

    @admin.display(description='В избранных')
    def get_count(self, obj):
        """
        Возвращает количество рецептов в избранном.
        """
        return obj.recipe.count()


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    """
    Админ-интерфейс для управления корзиной покупок.
    """

    list_display = ('id', 'user', 'get_recipe', 'get_count')
    empty_value_display = EMPTY

    @admin.display(description='Рецепты')
    def get_recipe(self, obj):
        """
        Возвращает список первых пяти рецептов в корзине.

        """
        return [f'{item["name"]} ' for item in obj.recipe.values('name')[:5]]

    @admin.display(description='В избранном')
    def get_count(self, obj):
        """
        Возвращает количество рецептов в корзине.
        """
        return obj.recipe.count()
