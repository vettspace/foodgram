from api.filters import IngredientFilter, RecipeFilter
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.db.models import Count, Exists, OuterRef, Sum, Value
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from recipes.models import (FavoriteRecipe, Ingredient, Recipe, ShoppingCart,
                            Subscribe, Tag)
from rest_framework import filters, generics, permissions, status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import SAFE_METHODS, AllowAny, IsAuthenticated
from rest_framework.response import Response

from . import constants
from .mixins import AdminOrReadOnlyMixin, RecipeAccessMixin
from .permissions import IsAuthorOrAdminOrReadOnly
from .serializers import (ChangePasswordSerializer, CreateUserSerializer,
                          IngredientSerializer, ObtainTokenSerializer,
                          RecipeCreateUpdateSerializer, RecipeReadSerializer,
                          SetAvatarSerializer, SubscriptionSerializer,
                          TagSerializer, UserSerializer)
from .utils import create_short_link, generate_shopping_cart_csv

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
    RecipeAccessMixin, generics.CreateAPIView, generics.DestroyAPIView
):
    """
    Представление для добавления и удаления рецепта в/из избранных.
    """

    serializer_class = RecipeReadSerializer
    permission_classes = (IsAuthenticated,)

    def create(self, request, *args, **kwargs):
        recipe = self.get_recipe()

        if FavoriteRecipe.objects.filter(
            user=request.user, recipe=recipe
        ).exists():
            return Response(
                {'errors': 'Рецепт уже добавлен в избранное'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        FavoriteRecipe.objects.create(user=request.user, recipe=recipe)

        serializer = self.get_serializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, *args, **kwargs):
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
    Представление для получения токена.
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

        @action(
            detail=False,
            permission_classes=(IsAuthenticated,),
            serializer_class=SubscriptionSerializer,
        )
        def subscriptions(self, request):
            """
            Получение списка подписок текущего пользователя.

            Параметры:
            - recipes_limit: опциональный параметр для ограничения рецептов
            """
            recipes_limit = request.GET.get('recipes_limit')
            if recipes_limit:
                try:
                    recipes_limit = int(recipes_limit)
                    if recipes_limit < 0:
                        return Response(
                            {
                                'error': 'recipes_limit must be >= 0',
                            },
                            status=status.HTTP_400_BAD_REQUEST,
                        )
                except ValueError:
                    return Response(
                        {'error': 'recipes_limit must be a valid integer'},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            user = request.user
            queryset = Subscribe.objects.filter(user=user).annotate(
                recipes_count=Count('author__recipe'),
                is_subscribed=Value(True),
            )
            pages = self.paginate_queryset(queryset)
            serializer = self.get_serializer(
                pages, many=True, context={'request': request}
            )
            return self.get_paginated_response(serializer.data)

    @action(
        detail=False,
        methods=['put'],
        permission_classes=[IsAuthenticated],
    )
    def upload_avatar(self, request):
        """Загрузка аватара пользователя."""
        serializer = SetAvatarSerializer(data=request.data)
        if serializer.is_valid():
            # Удаляем старый аватар, если он существует
            if request.user.avatar:
                request.user.avatar.delete()

            request.user.avatar = serializer.validated_data['avatar']
            request.user.save()

            response_serializer = UserSerializer(
                request.user, context={'request': request}
            )
            return Response(
                response_serializer.data, status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=False,
        methods=['delete'],
        permission_classes=[IsAuthenticated],
    )
    def delete_avatar(self, request):
        """Удаление аватара пользователя."""
        if request.user.avatar:
            request.user.avatar.delete()
            request.user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {'detail': 'Аватар отсутствует'}, status=status.HTTP_404_NOT_FOUND
        )


class RecipeViewSet(viewsets.ModelViewSet):
    """
    Представление для управления рецептами.

    list: Получение списка рецептов
    create: Создание нового рецепта
    retrieve: Получение конкретного рецепта
    update: Обновление рецепта
    partial_update: Частичное обновление рецепта
    destroy: Удаление рецепта
    """

    queryset = Recipe.objects.all()
    filterset_class = RecipeFilter
    http_method_names = ['get', 'post', 'patch', 'delete']

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

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'get_link']:
            permission_classes = [permissions.AllowAny]
        elif self.action == 'create':
            permission_classes = [permissions.IsAuthenticated]
        elif self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [IsAuthorOrAdminOrReadOnly]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipeReadSerializer
        return RecipeCreateUpdateSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(
        detail=True,
        methods=['get'],
        url_path='get-link',
        permission_classes=[AllowAny],
    )
    @action(
        detail=True,
        methods=['get'],
        url_path='get-link',
        permission_classes=[AllowAny],
    )
    def get_link(self, request, pk=None):
        """Получение прямой ссылки на рецепт."""
        try:
            recipe = self.get_object()
            direct_link = create_short_link(recipe.id, request)
            return Response(
                {'short-link': direct_link}, status=status.HTTP_200_OK
            )
        except Recipe.DoesNotExist:
            return Response(
                {'detail': 'Рецепт не найден'},
                status=status.HTTP_404_NOT_FOUND,
            )

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated],
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

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated],
        url_path='favorite',
    )
    def favorite(self, request, pk=None):
        """Добавление/удаление рецепта в избранное."""
        recipe = self.get_object()

        if request.method == 'POST':
            if FavoriteRecipe.objects.filter(
                user=request.user, recipe=recipe
            ).exists():
                return Response(
                    {'errors': 'Рецепт уже в избранном'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            FavoriteRecipe.objects.create(user=request.user, recipe=recipe)
            serializer = RecipeReadSerializer(
                recipe, context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

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

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated],
        url_path='shopping_cart',
    )
    def shopping_cart(self, request, pk=None):
        """Добавление/удаление рецепта в список покупок."""
        recipe = self.get_object()

        if request.method == 'POST':
            if ShoppingCart.objects.filter(
                user=request.user, recipe=recipe
            ).exists():
                return Response(
                    {'errors': 'Рецепт уже в списке покупок'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            ShoppingCart.objects.create(user=request.user, recipe=recipe)
            serializer = RecipeReadSerializer(
                recipe, context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        shopping_cart = ShoppingCart.objects.filter(
            user=request.user, recipe=recipe
        )
        if not shopping_cart.exists():
            return Response(
                {'errors': 'Рецепт не находится в списке покупок'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        shopping_cart.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TagViewSet(RecipeAccessMixin, viewsets.ModelViewSet):
    """Список тэгов."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class IngredientViewSet(AdminOrReadOnlyMixin, viewsets.ModelViewSet):
    """
    Представление для управления ингредиентами.
    """

    queryset = Ingredient.objects.all().order_by('name')
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    filterset_class = IngredientFilter
    search_fields = ('^name',)
    pagination_class = None

    def get_queryset(self):
        queryset = super().get_queryset()
        name = self.request.query_params.get('name')
        search = self.request.query_params.get('search')

        if name:
            queryset = queryset.filter(name__icontains=name)
        if search:
            queryset = queryset.filter(name__icontains=search)

        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


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
        return Response(status=status.HTTP_204_NO_CONTENT)
    return Response(
        serializer.errors,
        status=status.HTTP_400_BAD_REQUEST,
    )
