import django_filters as filters
from django.core.exceptions import ValidationError

from recipes.models import Ingredient, Recipe
from users.models import User


class TagsMultipleChoiceField(filters.fields.MultipleChoiceField):
    """
    Кастомное поле для обработки валидации множественного выбора тегов.
    """

    def validate(self, value):
        """
        Проверяет переданное значение на соответствие обязательным
        и допустимым вариантам.
        """
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


class TagsFilter(filters.AllValuesMultipleFilter):
    """
    Класс фильтра для обработки множественных значений тегов.
    """

    field_class = TagsMultipleChoiceField


class IngredientFilter(filters.FilterSet):
    """
    Фильтры для ингредиентов по имени.
    """

    name = filters.CharFilter(lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ('name',)


class RecipeFilter(filters.FilterSet):
    """
    Фильтры по различным критериям.
    """

    author = filters.ModelChoiceFilter(queryset=User.objects.all())
    is_in_shopping_cart = filters.BooleanFilter(
        widget=filters.widgets.BooleanWidget(), label='В корзине'
    )
    is_favorited = filters.BooleanFilter(
        widget=filters.widgets.BooleanWidget(), label='В избранном'
    )
    tags = TagsFilter(field_name='tags__slug', label='Ссылка')

    class Meta:
        model = Recipe
        fields = ['is_favorited', 'is_in_shopping_cart', 'author', 'tags']
