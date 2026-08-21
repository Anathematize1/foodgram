"""Вьюсеты и вспомогательные представления API."""
from django.db.models import BooleanField, Exists, OuterRef, Value
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from recipes.models import Favorite, Ingredient, Recipe, ShoppingCart, Tag
from users.models import Subscription, User

from .filters import IngredientFilter, RecipeFilter
from .mixins import AddDeleteRecipeMixin
from .pagination import LimitPageNumberPagination
from .permissions import IsAuthorOrReadOnly
from .serializers import (
    AvatarSerializer,
    IngredientSerializer,
    RecipeReadSerializer,
    RecipeWriteSerializer,
    TagSerializer,
    UserSerializer,
    UserWithRecipesSerializer,
)
from .utils import get_shopping_list_text


class UserViewSet(DjoserUserViewSet):
    """Пользователи: регистрация, профиль, аватар и подписки."""

    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = LimitPageNumberPagination

    def get_permissions(self):
        """Разрешает чтение и регистрацию без токена."""
        if self.action in (
            'list',
            'retrieve',
            'create',
            'reset_password',
            'reset_password_confirm',
            'activation',
            'resend_activation',
        ):
            return (AllowAny(),)
        return (IsAuthenticated(),)

    @action(
        methods=('put', 'delete'),
        detail=False,
        permission_classes=(IsAuthenticated,),
        url_path='me/avatar',
    )
    def avatar(self, request):
        """Добавляет или удаляет аватар текущего пользователя."""
        user = request.user
        if request.method == 'PUT':
            serializer = AvatarSerializer(user, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        if not user.avatar:
            return Response(
                {'avatar': 'Аватар не установлен.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user.avatar.delete(save=True)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=('get',),
        detail=False,
        permission_classes=(IsAuthenticated,),
    )
    def subscriptions(self, request):
        """Возвращает авторов, на которых подписан пользователь."""
        queryset = User.objects.filter(
            subscribers__user=request.user,
        ).prefetch_related('recipes')
        pages = self.paginate_queryset(queryset)
        serializer = UserWithRecipesSerializer(
            pages,
            many=True,
            context={'request': request},
        )
        return self.get_paginated_response(serializer.data)

    @action(
        methods=('post', 'delete'),
        detail=True,
        permission_classes=(IsAuthenticated,),
    )
    def subscribe(self, request, **kwargs):
        """Подписывает или отписывает текущего пользователя от автора."""
        author = self.get_object()
        user = request.user
        if request.method == 'POST':
            if user == author:
                return Response(
                    {'errors': 'Нельзя подписаться на самого себя.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            _, created = Subscription.objects.get_or_create(
                user=user,
                author=author,
            )
            if not created:
                return Response(
                    {'errors': 'Вы уже подписаны на этого пользователя.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            serializer = UserWithRecipesSerializer(
                author,
                context={'request': request},
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        deleted, _ = Subscription.objects.filter(
            user=user,
            author=author,
        ).delete()
        if not deleted:
            return Response(
                {'errors': 'Вы не подписаны на этого пользователя.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Список и получение тегов."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Список и получение ингредиентов."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    filterset_class = IngredientFilter
    pagination_class = None


class RecipeViewSet(AddDeleteRecipeMixin, viewsets.ModelViewSet):
    """Рецепты, избранное, список покупок и короткие ссылки."""

    queryset = Recipe.objects.all()
    permission_classes = (IsAuthorOrReadOnly,)
    filterset_class = RecipeFilter
    http_method_names = ('get', 'post', 'patch', 'delete', 'head', 'options')

    def get_queryset(self):
        queryset = Recipe.objects.select_related('author').prefetch_related(
            'tags',
            'recipe_ingredients__ingredient',
        ).distinct()
        user = self.request.user
        if user.is_authenticated:
            return queryset.annotate(
                is_favorited_ann=Exists(
                    Favorite.objects.filter(
                        user=user,
                        recipe=OuterRef('pk'),
                    ),
                ),
                is_in_shopping_cart_ann=Exists(
                    ShoppingCart.objects.filter(
                        user=user,
                        recipe=OuterRef('pk'),
                    ),
                ),
            )
        false_value = Value(False, output_field=BooleanField())
        return queryset.annotate(
            is_favorited_ann=false_value,
            is_in_shopping_cart_ann=false_value,
        )

    def get_serializer_class(self):
        if self.action in ('create', 'partial_update'):
            return RecipeWriteSerializer
        return RecipeReadSerializer

    @action(
        methods=('post', 'delete'),
        detail=True,
        permission_classes=(IsAuthenticated,),
    )
    def favorite(self, request, pk=None):
        """Добавляет рецепт в избранное или удаляет его оттуда."""
        return self.add_delete_recipe(
            request,
            Favorite,
            'Рецепт уже в избранном.',
            'Рецепта нет в избранном.',
        )

    @action(
        methods=('post', 'delete'),
        detail=True,
        permission_classes=(IsAuthenticated,),
    )
    def shopping_cart(self, request, pk=None):
        """Добавляет рецепт в список покупок или удаляет его оттуда."""
        return self.add_delete_recipe(
            request,
            ShoppingCart,
            'Рецепт уже в списке покупок.',
            'Рецепта нет в списке покупок.',
        )

    @action(
        methods=('get',),
        detail=True,
        permission_classes=(AllowAny,),
        url_path='get-link',
    )
    def get_link(self, request, pk=None):
        """Возвращает короткую ссылку на рецепт."""
        recipe = self.get_object()
        short_link = request.build_absolute_uri(f'/s/{recipe.short_code}')
        return Response({'short-link': short_link})

    @action(
        methods=('get',),
        detail=False,
        permission_classes=(IsAuthenticated,),
    )
    def download_shopping_cart(self, request):
        """Отдаёт текстовый файл со списком покупок."""
        content = get_shopping_list_text(request.user)
        response = HttpResponse(
            content,
            content_type='text/plain; charset=utf-8',
        )
        response['Content-Disposition'] = (
            'attachment; filename="shopping-list.txt"'
        )
        return response


def recipe_short_link(request, code):
    """Перенаправляет с короткой ссылки на страницу рецепта."""
    recipe = get_object_or_404(Recipe, short_code=code)
    return redirect(f'/recipes/{recipe.id}')
