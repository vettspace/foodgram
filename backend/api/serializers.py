from django.contrib.auth import get_user_model
from drf_base64.fields import Base64ImageField
from rest_framework import serializers

from recipes.models import (FavoriteRecipe, Ingredient, Recipe,
                            RecipeIngredient, ShoppingCart, Subscribe, Tag)

from . import constants
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
    """Сериализатор для редактирования ингредиентов в рецепте."""

    id = serializers.IntegerField()
    amount = serializers.IntegerField(
        min_value=constants.MIN_AMOUNT,
        max_value=constants.MAX_AMOUNT,
        error_messages={
            'min_value': constants.INGREDIENT_AMOUNT_MIN_ERROR,
            'max_value': constants.INGREDIENT_AMOUNT_MAX_ERROR,
        },
    )

    class Meta:
        model = Ingredient
        fields = ('id', 'amount')


class RecipeCreateUpdateSerializer(
    IngredientCreationMixin, serializers.ModelSerializer
):
    """Сериализатор для создания и обновления рецептов."""

    image = Base64ImageField(max_length=None, use_url=True)
    name = serializers.CharField(
        max_length=constants.RECIPE_NAME_LENGTH,
        required=True,
        allow_blank=False,
        error_messages={
            'blank': constants.RECIPE_NAME_EMPTY,
            'required': constants.RECIPE_NAME_REQUIRED,
        },
    )
    text = serializers.CharField(
        required=True,
        allow_blank=False,
        error_messages={
            'blank': constants.RECIPE_TEXT_EMPTY,
            'required': constants.RECIPE_TEXT_REQUIRED,
        },
    )
    cooking_time = serializers.IntegerField(
        min_value=constants.MIN_COOKING_TIME,
        max_value=constants.MAX_COOKING_TIME,
        error_messages={
            'min_value': constants.COOKING_TIME_ERROR,
            'max_value': constants.COOKING_TIME_ERROR,
        },
    )
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all(),
        error_messages={
            'does_not_exist': constants.TAG_NOT_EXISTS,
            'incorrect_type': constants.TAG_INCORRECT_TYPE,
        },
    )
    ingredients = EditIngredientsSerializer(
        many=True,
        error_messages={
            'empty': constants.INGREDIENTS_REQUIRED_ERROR,
            'invalid': constants.INVALID_INGREDIENTS_ERROR,
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
        """Проверка данных рецепта."""

        # Проверка ингредиентов
        ingredients = data.get('ingredients', [])
        if not ingredients:
            raise serializers.ValidationError(
                {'ingredients': constants.NO_INGREDIENTS_ERROR}
            )

        ingredient_ids = set()
        for item in ingredients:
            ingredient_id = item['id']
            if ingredient_id in ingredient_ids:
                raise serializers.ValidationError(
                    {'ingredients': constants.DUPLICATE_INGREDIENTS_ERROR}
                )
            ingredient_ids.add(ingredient_id)

            # Проверяем существование ингредиента
            try:
                _ = Ingredient.objects.get(id=ingredient_id)
            except Ingredient.DoesNotExist as exc:
                raise serializers.ValidationError(
                    {'ingredients': constants.INGREDIENT_NOT_EXIST_ERROR}
                ) from exc

        # Проверка тегов
        tags = data.get('tags', [])
        if not tags:
            raise serializers.ValidationError(
                {'tags': constants.NO_TAGS_ERROR}
            )

        if len(tags) != len(set(tags)):
            raise serializers.ValidationError(
                {'tags': constants.DUPLICATE_TAGS_ERROR}
            )

        return data

    def validate_name(self, value):
        if len(value.strip()) == 0:
            raise serializers.ValidationError(constants.RECIPE_NAME_EMPTY)
        return value.strip()

    def validate_text(self, value):
        if len(value.strip()) == 0:
            raise serializers.ValidationError(constants.RECIPE_TEXT_EMPTY)
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
        if value.size > constants.MAX_AVATAR_SIZE_BYTES:
            raise serializers.ValidationError(
                f'{constants.AVATAR_ERROR} '
                f'{constants.MAX_AVATAR_SIZE_BYTES // (1024 * 1024)}MB'
            )
        return value


class RecipeShortLinkSerializer(serializers.Serializer):
    """Сериализатор для создания ссылки на рецепт."""

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
    """Сериализатор для отображения подписок."""

    email = serializers.EmailField(source='author.email')
    id = serializers.IntegerField(source='author.id')
    username = serializers.CharField(source='author.username')
    first_name = serializers.CharField(source='author.first_name')
    last_name = serializers.CharField(source='author.last_name')
    is_subscribed = serializers.BooleanField(default=True)
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = Subscribe
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
        )
        read_only_fields = fields

    def get_recipes_count(self, obj):
        """Получение количества рецептов автора."""
        return obj.author.recipe.count()

    def get_recipes(self, obj):
        """Получение рецептов автора с учетом лимита."""
        request = self.context.get('request')
        if not request:
            return []

        recipes = obj.author.recipe.all()
        recipes_limit = request.query_params.get('recipes_limit')

        if recipes_limit is not None:
            try:
                recipes_limit = int(recipes_limit)
                recipes = recipes[:recipes_limit]
            except ValueError:
                pass

        return SubscribedRecipeSerializer(
            recipes, many=True, context={'request': request}
        ).data


class FavoriteRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для избранных рецептов."""

    recipe = serializers.PrimaryKeyRelatedField(queryset=Recipe.objects.all())

    class Meta:
        model = FavoriteRecipe
        fields = ('recipe',)

    def validate(self, data):
        user = self.context['request'].user
        recipe = data['recipe']

        if user.favorite_recipes.filter(recipe=recipe).exists():
            raise serializers.ValidationError(
                {'errors': constants.ERROR_RECIPE_ALREADY_FAVORITED}
            )
        return data

    def create(self, validated_data):
        user = self.context['request'].user
        recipe = validated_data['recipe']
        return FavoriteRecipe.objects.create(user=user, recipe=recipe)


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Сериализатор для корзины покупок."""

    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe')

    def validate(self, data):
        user = self.context['request'].user
        recipe = data['recipe']

        if user.shopping_cart.recipe.filter(id=recipe.id).exists():
            raise serializers.ValidationError(
                {'errors': constants.RECIPE_ALREADY_IN_CART}
            )
        return data
