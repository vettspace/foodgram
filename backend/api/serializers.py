from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.hashers import make_password
from django.shortcuts import get_object_or_404
from drf_base64.fields import Base64ImageField
from rest_framework import serializers

from recipes.models import Ingredient, Recipe, RecipeIngredient, Subscribe, Tag

from . import constants
from .mixins import (IngredientCreationMixin, PasswordValidationMixin,
                     SubscriptionMixin)

User = get_user_model()


class ObtainTokenSerializer(serializers.Serializer):
    """
    Сериализатор для получения токена с использованием email и пароля.
    """

    email = serializers.CharField(label='Email', write_only=True)
    password = serializers.CharField(
        label='Пароль',
        style=constants.PASSWORD_STYLE,
        trim_whitespace=False,
        write_only=True,
    )
    token = serializers.CharField(label='Токен', read_only=True)

    def validate(self, data):
        email = data.get('email')
        password = data.get('password')
        if email and password:
            user = authenticate(
                request=self.context.get('request'),
                email=email,
                password=password,
            )
            if not user:
                raise serializers.ValidationError(
                    constants.AUTH_ERROR_MESSAGE, code='authorization'
                )
        else:
            raise serializers.ValidationError(
                constants.ERROR_MISSING_CREDENTIALS, code='authorization'
            )
        data['user'] = user
        return data


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


class CreateUserSerializer(
    PasswordValidationMixin, serializers.ModelSerializer
):
    """
    Сериализатор для создания нового пользователя.
    """

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


class ChangePasswordSerializer(serializers.Serializer):
    """
    Сериализатор для изменения пароля пользователя.
    """

    new_password = serializers.CharField(label='Новый пароль')
    current_password = serializers.CharField(label='Текущий пароль')

    def validate_current_password(self, current_password):
        user = self.context['request'].user
        if not authenticate(username=user.email, password=current_password):
            raise serializers.ValidationError(
                constants.AUTH_ERROR_MESSAGE, code='authorization'
            )
        return current_password

    def validate_new_password(self, new_password):
        from django.contrib.auth.password_validation import validate_password

        validate_password(new_password)
        return new_password

    def create(self, validated_data):
        user = self.context['request'].user
        user.password = make_password(validated_data.get('new_password'))
        user.save()
        return validated_data


class TagSerializer(serializers.ModelSerializer):
    """
    Сериализатор для отображения тегов.
    """

    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


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
    Сериализатор для создания и редактирования рецептов.
    """

    image = Base64ImageField(max_length=None, use_url=True)
    tags = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Tag.objects.all()
    )
    ingredients = EditIngredientsSerializer(many=True)

    class Meta:
        model = Recipe
        fields = '__all__'
        read_only_fields = ('author',)

    def validate(self, data):
        ingredients = data['ingredients']
        ingredient_ids = set()
        for item in ingredients:
            ingredient = get_object_or_404(Ingredient, id=item['id'])
            if ingredient.id in ingredient_ids:
                raise serializers.ValidationError(
                    constants.ERROR_DUPLICATE_INGREDIENT
                )
            ingredient_ids.add(ingredient.id)

        if not data['tags']:
            raise serializers.ValidationError(constants.ERROR_NO_TAGS)

        return data

    def validate_cooking_time(self, cooking_time):
        if cooking_time < 1:
            raise serializers.ValidationError(constants.ERROR_COOKING_TIME)
        return cooking_time

    def validate_ingredients(self, ingredients):
        if not ingredients:
            raise serializers.ValidationError(constants.ERROR_MIN_INGREDIENTS)
        for ingredient in ingredients:
            if ingredient.get('amount') < 1:
                raise serializers.ValidationError(
                    constants.ERROR_INGREDIENT_AMOUNT
                )
        return ingredients

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
    recipes = serializers.SerializerMethodField()
    is_subscribed = serializers.BooleanField(read_only=True)
    recipes_count = serializers.IntegerField(read_only=True)

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

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.GET.get('recipes_limit')
        recipes = (
            obj.author.recipe.all()[: int(limit)]
            if limit
            else obj.author.recipe.all()
        )
        return SubscribedRecipeSerializer(recipes, many=True).data
