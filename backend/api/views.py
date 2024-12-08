from api.filters import IngredientFilter, RecipeFilter
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.db.models import Count, Exists, OuterRef, Sum, Value
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from recipes.models import (FavoriteRecipe, Ingredient, Recipe, ShoppingCart,
                            Subscribe, Tag)
from rest_framework import generics, serializers, status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import (SAFE_METHODS, AllowAny,
                                        IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response

from . import constants
from .mixins import AdminOrReadOnlyMixin, RecipeAccessMixin
from .serializers import (ChangePasswordSerializer, CreateUserSerializer,
                          IngredientSerializer, ObtainTokenSerializer,
                          RecipeCreateUpdateSerializer, RecipeReadSerializer,
                          SubscriptionSerializer, TagSerializer,
                          UserSerializer)
from .utils import generate_shopping_cart_csv

User = get_user_model()


class SubscriptionView(
    generics.ListCreateAPIView, generics.RetrieveDestroyAPIView
):
    """
    Представление для подписки и отписки от пользователя.
    """

    permission_classes = (IsAuthenticated,)
    serializer_class = SubscriptionSerializer
    lookup_field = 'user_id'

    def get_queryset(self):
        return (
            Subscribe.objects.filter(user=self.request.user)
            .select_related('author')
            .annotate(
                recipes_count=Count('author__recipe'),
                is_subscribed=Value(True),
            )
        )

    def get_object(self):
        user = self.get_user()
        return get_object_or_404(
            Subscribe, user=self.request.user, author=user
        )

    def get_user(self):
        user_id = self.kwargs['user_id']
        user = get_object_or_404(User, id=user_id)
        self.check_object_permissions(self.request, user)
        return user

    def create(self, request, *args, **kwargs):
        user = self.get_user()
        if request.user.id == user.id:
            return Response(
                {'errors': constants.ERROR_SELF_SUBSCRIBE},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if Subscribe.objects.filter(user=request.user, author=user).exists():
            return Response(
                {'errors': constants.ERROR_ALREADY_SUBSCRIBED},
                status=status.HTTP_400_BAD_REQUEST,
            )
        subscription = Subscribe.objects.create(user=request.user, author=user)
        serializer = self.get_serializer(subscription)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_destroy(self, instance):
        instance.delete()


class FavoriteRecipeView(
    RecipeAccessMixin,
    generics.ListCreateAPIView,
    generics.RetrieveDestroyAPIView,
):
    """
    Представление для добавления и удаления рецепта в/из избранных.
    """

    serializer_class = RecipeReadSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return Recipe.objects.all()

    def create(self, request, *args, **kwargs):
        try:
            recipe = self.get_recipe()
            if FavoriteRecipe.objects.filter(
                user=request.user, recipe=recipe
            ).exists():
                return Response(
                    {'errors': 'Рецепт уже добавлен в избранное'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            FavoriteRecipe.objects.create(user=request.user, recipe=recipe)

            response_data = {
                'id': recipe.id,
                'name': recipe.name,
                'image': (
                    request.build_absolute_uri(recipe.image.url)
                    if recipe.image
                    else None
                ),
                'cooking_time': recipe.cooking_time,
            }

            return Response(response_data, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response(
                {'errors': str(e)}, status=status.HTTP_400_BAD_REQUEST
            )

    def destroy(self, request, *args, **kwargs):
        try:
            recipe = self.get_recipe()
            favorite = FavoriteRecipe.objects.filter(
                user=request.user, recipe=recipe
            )

            if not favorite.exists():
                return Response(
                    {'errors': 'Рецепт не находится в избранном'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            favorite.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        except Exception as e:
            return Response(
                {'errors': str(e)}, status=status.HTTP_400_BAD_REQUEST
            )


class ShoppingCartView(
    RecipeAccessMixin,
    generics.ListCreateAPIView,
    generics.RetrieveDestroyAPIView,
):
    """Добавление и удаление рецепта в/из корзины."""

    serializer_class = RecipeReadSerializer

    def get_queryset(self):
        return Recipe.objects.all()

    def create(self, request, *args, **kwargs):
        instance = self.get_recipe()
        request.user.shopping_cart.recipe.add(instance)
        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_recipe()
        request.user.shopping_cart.recipe.remove(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


class CustomAuthToken(ObtainAuthToken):
    """
    Представление для авторизации пользователя.
    """

    serializer_class = ObtainTokenSerializer
    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(
            data=request.data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response({'auth_token': token.key})


class CustomUserViewSet(UserViewSet):
    """
    Представление для управления пользователями.
    """

    serializer_class = UserSerializer

    def get_permissions(self):
        if self.action in ['create', 'list', 'retrieve']:
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return User.objects.annotate(
                is_subscribed=Exists(
                    self.request.user.follower.filter(author=OuterRef('id'))
                )
            ).prefetch_related('follower', 'following')
        return User.objects.annotate(is_subscribed=Value(False))

    def get_serializer_class(self):
        return (
            CreateUserSerializer
            if self.request.method.lower() == 'post'
            else UserSerializer
        )

    def perform_create(self, serializer):
        password = make_password(self.request.data['password'])
        serializer.save(password=password)

    @action(detail=False, permission_classes=(IsAuthenticated,))
    def subscriptions(self, request):
        user = request.user
        queryset = Subscribe.objects.filter(user=user).annotate(
            recipes_count=Count('author__recipe'),
            is_subscribed=Value(True),
        )
        pages = self.paginate_queryset(queryset)
        serializer = SubscriptionSerializer(
            pages, many=True, context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=False,
        methods=['post', 'put'],
        permission_classes=[IsAuthenticated],
    )
    def upload_avatar(self, request):
        """Представление для загрузки аватара пользователя."""
        if 'avatar' not in request.data:
            return Response(
                {'error': 'Field "avatar" is required'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = request.user
        serializer = self.get_serializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {'avatar': serializer.data['avatar']},
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=False, methods=['delete'], permission_classes=[IsAuthenticated]
    )
    def delete_avatar(self, request):
        """Представление для удаления аватара пользователя."""
        user = request.user
        user.avatar.delete(save=True)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False, methods=['get'], permission_classes=[IsAuthenticated]
    )
    def get_avatar(self, request):
        """Представление для получения аватара пользователя."""
        user = request.user
        if user.avatar:
            return Response(
                {'avatar': request.build_absolute_uri(user.avatar.url)},
                status=status.HTTP_200_OK,
            )
        return Response(
            {'message': 'Avatar not found'}, status=status.HTTP_400_BAD_REQUEST
        )


class RecipeViewSet(viewsets.ModelViewSet):
    """
    Представление для управления рецептами.
    """

    queryset = Recipe.objects.all()
    filterset_class = RecipeFilter
    permission_classes = (IsAuthenticatedOrReadOnly,)

    def get_serializer_class(self):
        return (
            RecipeReadSerializer
            if self.request.method in SAFE_METHODS
            else RecipeCreateUpdateSerializer
        )

    def get_queryset(self):
        queryset = (
            Recipe.objects.all()
            .select_related('author')
            .prefetch_related('tags', 'ingredients')
        )
        if self.request.user.is_authenticated:
            queryset = queryset.annotate(
                is_favorited=Exists(
                    FavoriteRecipe.objects.filter(
                        user=self.request.user, recipe=OuterRef('id')
                    )
                ),
                is_in_shopping_cart=Exists(
                    ShoppingCart.objects.filter(
                        user=self.request.user, recipe=OuterRef('id')
                    )
                ),
            )
        else:
            queryset = queryset.annotate(
                is_in_shopping_cart=Value(False), is_favorited=Value(False)
            )
        return queryset

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=True, methods=['get'], url_path='get-link')
    def get_link(self, request, pk=None):
        """
        Представление для получения ссылки на рецепт.
        """
        recipe = self.get_object()
        link = request.build_absolute_uri(f'/recipes/{recipe.id}/')
        return Response({'link': link})

    @action(
        detail=False, methods=['get'], permission_classes=(IsAuthenticated,)
    )
    def download_shopping_cart(self, request):
        """
        Представление для скачивания списка покупок в формате CSV.
        """
        shopping_cart = (
            request.user.shopping_cart.recipe.values(
                'ingredients__name', 'ingredients__measurement_unit'
            )
            .annotate(amount=Sum('recipe__amount'))
            .order_by()
        )
        return generate_shopping_cart_csv(shopping_cart)

    def update(self, request, *args, **kwargs):
        try:
            return super().update(request, *args, **kwargs)
        except serializers.ValidationError as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request, *args, **kwargs):
        try:
            return super().partial_update(request, *args, **kwargs)
        except serializers.ValidationError as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)


class TagViewSet(RecipeAccessMixin, viewsets.ModelViewSet):
    """Список тэгов."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientViewSet(AdminOrReadOnlyMixin, viewsets.ModelViewSet):
    """
    Представление для управления ингредиентами.
    """

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filterset_class = IngredientFilter


@api_view(['post'])
@permission_classes([IsAuthenticated])
def change_password(request):
    """
    Изменяет пароль пользователя.
    """
    serializer = ChangePasswordSerializer(
        data=request.data, context={'request': request}
    )
    if serializer.is_valid():
        serializer.save()
        return Response(
            {'message': constants.MESSAGE_PASSWORD_CHANGED},
            status=status.HTTP_204_NO_CONTENT,
        )
    return Response(
        {'error': constants.ERROR_INVALID_DATA},
        status=status.HTTP_400_BAD_REQUEST,
    )
