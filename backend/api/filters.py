from django.core.exceptions import ValidationError
from django.forms import MultipleChoiceField
from django_filters import rest_framework as filters

from recipes.models import Ingredient, Recipe
from users.models import User


class TagsMultipleChoiceField(MultipleChoiceField):
    """
    Кастомное поле для обработки валидации множественного выбора тегов.
    """

    def validate(self, value):
        if self.required and not value:
            raise ValidationError(
                self.error_messages['required'], code='required'
            )
        for val in value:
            if val in self.choices and not self.valid_value(val):
                raise ValidationError(
                    self.error_messages['invalid_choice'],
                    code='invalid_choice',
                    params={'value': val},
                )


class TagsFilter(MultipleChoiceField):
    """
    Класс фильтра для обработки множественных значений тегов.
    """

    field_class = TagsMultipleChoiceField


class IngredientFilter(filters.FilterSet):
    """
    Фильтр для ингредиентов.
    """
    name = filters.CharFilter(
        field_name='name',
        lookup_expr='istartswith',
        help_text='Поиск по названию ингредиента'
    )

    class Meta:
        model = Ingredient
        fields = ('name',)


class RecipeFilter(filters.FilterSet):
    """
    Фильтры для рецептов.
    """

    tags = filters.AllValuesMultipleFilter(
        field_name='tags__slug', help_text='Фильтрация по тегам'
    )
    author = filters.ModelChoiceFilter(
        queryset=User.objects.all(), help_text='Фильтрация по автору'
    )
    is_in_shopping_cart = filters.BooleanFilter(
        label='В корзине',
        method='filter_is_in_shopping_cart',
        help_text='Фильтрация по наличию в списке покупок',
    )
    is_favorited = filters.BooleanFilter(
        label='В избранном',
        method='filter_is_favorited',
        help_text='Фильтрация по наличию в избранном',
    )

    class Meta:
        model = Recipe
        fields = ['is_favorited', 'is_in_shopping_cart', 'author', 'tags']

    def filter_is_favorited(self, queryset, name, value):
        user = self.request.user
        if value and user.is_authenticated:
            return queryset.filter(favorited_by__user=user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        user = self.request.user
        if value and user.is_authenticated:
            return queryset.filter(shopping_cart__user=user)
        return queryset
