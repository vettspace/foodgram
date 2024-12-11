from django.contrib.auth import get_user_model
from drf_base64.fields import Base64ImageField
from recipes.models import Ingredient, Recipe, RecipeIngredient, Subscribe, Tag
from rest_framework import serializers

from .mixins import (IngredientCreationMixin, PasswordValidationMixin,
                     SubscriptionMixin)

User = get_user_model()


class UserSerializer(SubscriptionMixin, serializers.ModelSerializer):
    """
    Сериализатор для отображения списка пользователей.
    """

    avatar = Base64ImageField(required=False)
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar',
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return request.user.follower.filter(author=obj).exists()


class CreateUserSerializer(
    PasswordValidationMixin, serializers.ModelSerializer
):
    """
    Сериализатор для создания нового пользователя.
    """

    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'password',
        )


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = (
            'id',
            'name',
            'slug',
        )


class IngredientSerializer(serializers.ModelSerializer):
    """
    Сериализатор для отображения ингредиентов.
    """

    class Meta:
        model = Ingredient
        fields = '__all__'


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """
    Сериализатор для отображения ингредиентов в рецепте.
    """

    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeAuthorSerializer(SubscriptionMixin, serializers.ModelSerializer):
    """
    Сериализатор для отображения информации о пользователе в рецепте.
    """

    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
        )


class EditIngredientsSerializer(serializers.ModelSerializer):
    """
    Сериализатор для редактирования ингредиентов в рецепте.
    """

    id = serializers.IntegerField()
    amount = serializers.IntegerField()

    class Meta:
        model = Ingredient
        fields = ('id', 'amount')


class RecipeCreateUpdateSerializer(
    IngredientCreationMixin, serializers.ModelSerializer
):
    """
    Сериализатор для создания и обновления рецептов.
    """

    image = Base64ImageField(max_length=None, use_url=True)
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all(),
        error_messages={
            'does_not_exist': 'Тег с идентификатором {pk_value} не существует',
            'incorrect_type': 'Некорректный тип данных. Ожидался ID тега',
        },
    )
    ingredients = EditIngredientsSerializer(
        many=True,
        error_messages={
            'empty': 'Это поле обязательно.',
            'invalid': 'Некорректные данные. Ожидался список ингредиентов.',
        },
    )

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'name',
            'image',
            'text',
            'cooking_time',
        )
        read_only_fields = ('author',)

    def validate(self, data):
        # Проверка ингредиентов
        ingredients = data.get('ingredients', [])
        if not ingredients:
            raise serializers.ValidationError(
                {'ingredients': 'Необходимо указать хотя бы один ингредиент.'}
            )

        ingredient_ids = set()
        for item in ingredients:
            ingredient_id = item['id']
            if ingredient_id in ingredient_ids:
                raise serializers.ValidationError(
                    {
                        'ingredients': print(
                            'Ингредиент указан более одного раза.'
                        )
                    }
                )
            ingredient_ids.add(ingredient_id)

            # Проверяем существование ингредиента
            try:
                _ = Ingredient.objects.get(id=ingredient_id)
            except Ingredient.DoesNotExist as exc:
                raise serializers.ValidationError(
                    {'ingredients': 'Ингредиент не существует.'}
                ) from exc

            # Проверка количества
            amount = item.get('amount', 0)
            if amount <= 0:
                raise serializers.ValidationError(
                    {'ingredients': 'Ингридиентов должно быть больше нуля.'}
                )

        # Проверка тегов
        tags = data.get('tags', [])
        if not tags:
            raise serializers.ValidationError(
                {'tags': 'Необходимо указать хотя бы один тег.'}
            )

        if len(tags) != len(set(tags)):
            raise serializers.ValidationError(
                {'tags': 'Теги не должны повторяться.'}
            )

        # Проверка времени приготовления
        cooking_time = data.get('cooking_time', 0)
        if cooking_time <= 0:
            raise serializers.ValidationError(
                {'cooking_time': 'Время приготовления должно быть > 0.'}
            )

        return data

    def validate_name(self, value):
        if len(value.strip()) == 0:
            raise serializers.ValidationError(
                'Название рецепта не может быть пустым.'
            )
        return value.strip()

    def validate_text(self, value):
        if len(value.strip()) == 0:
            raise serializers.ValidationError(
                'Описание рецепта не может быть пустым.'
            )
        return value.strip()

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        self.create_ingredients(ingredients, recipe)
        return recipe

    def update(self, instance, validated_data):
        if 'ingredients' in validated_data:
            ingredients = validated_data.pop('ingredients')
            instance.ingredients.clear()
            self.create_ingredients(ingredients, instance)
        if 'tags' in validated_data:
            instance.tags.set(validated_data.pop('tags'))
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        return RecipeReadSerializer(instance, context=self.context).data


class SetAvatarSerializer(serializers.Serializer):
    """Сериализатор для загрузки аватара."""

    avatar = Base64ImageField(required=True)

    class Meta:
        fields = ('avatar',)

    def validate_avatar(self, value):
        if value.size > 2 * 1024 * 1024:  # 2MB
            raise serializers.ValidationError(
                'Размер изображения не должен превышать 2MB'
            )
        return value


class RecipeShortLinkSerializer(serializers.Serializer):
    """Сериализатор для короткой ссылки на рецепт."""

    short_link = serializers.URLField()

    def to_representation(self, instance):
        """
        Возвращает короткую ссылку на рецепт.
        """
        return {'short-link': instance['short_link']}


class RecipeReadSerializer(serializers.ModelSerializer):
    """
    Сериализатор для отображения рецептов.
    """

    image = Base64ImageField()
    tags = TagSerializer(many=True, read_only=True)
    author = RecipeAuthorSerializer(
        read_only=True, default=serializers.CurrentUserDefault()
    )
    ingredients = RecipeIngredientSerializer(
        many=True, source='recipe', read_only=True
    )
    is_favorited = serializers.BooleanField(read_only=True)
    is_in_shopping_cart = serializers.BooleanField(read_only=True)

    class Meta:
        model = Recipe
        fields = '__all__'


class SubscribedRecipeSerializer(serializers.ModelSerializer):
    """
    Сериализатор для отображения рецептов в подписках.
    """

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class SubscriptionSerializer(serializers.ModelSerializer):
    """
    Сериализатор для отображения подписок.
    """

    id = serializers.IntegerField(source='author.id')
    email = serializers.EmailField(source='author.email')
    username = serializers.CharField(source='author.username')
    first_name = serializers.CharField(source='author.first_name')
    last_name = serializers.CharField(source='author.last_name')
    is_subscribed = serializers.BooleanField(default=True)
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Subscribe
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
        )

    def get_recipes(self, obj):
        """
        Возвращает список рецептов автора.
        """
        request = self.context.get('request')
        if not request:
            return []

        recipes = obj.author.recipe.all()
        try:
            recipes_limit = request.GET.get('recipes_limit')
            if recipes_limit:
                recipes_limit = int(recipes_limit)
                if recipes_limit < 0:
                    raise ValueError('recipes_limit must be positive')
                recipes = recipes[:recipes_limit]
        except ValueError:
            # Если возникла ошибка преобразования или отрицательное значение,
            # игнорируем параметр recipes_limit
            pass

        return SubscribedRecipeSerializer(recipes, many=True).data
