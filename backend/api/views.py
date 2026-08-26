"""Вьюсеты и вспомогательные представления API."""
from django.db.models import (
    BooleanField,
    Count,
    Exists,
    OuterRef,
    Prefetch,
    Value,
)
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
from .pagination import LimitPageNumberPagination
from .permissions import IsAuthorOrReadOnly
from .serializers import (
    AvatarSerializer,
    FavoriteSerializer,
    IngredientSerializer,
    RecipeReadSerializer,
    RecipeWriteSerializer,
    ShoppingCartSerializer,
    SubscriptionSerializer,
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

    def get_queryset(self):
        queryset = User.objects.all()
        user = self.request.user
        false_value = Value(False, output_field=BooleanField())
        if user.is_authenticated:
            return queryset.annotate(
                is_subscribed=Exists(
                    Subscription.objects.filter(
                        user=user,
                        author=OuterRef('pk'),
                    ),
                ),
            )
        return queryset.annotate(is_subscribed=false_value)

    def get_instance(self):
        self.request.user.is_subscribed = False
        return self.request.user

    def get_permissions(self):
        if self.action == 'me':
            return (IsAuthenticated(),)
        return super().get_permissions()

    @action(
        methods=('put',),
        detail=False,
        permission_classes=(IsAuthenticated,),
        url_path='me/avatar',
    )
    def avatar(self, request):
        """Добавляет аватар текущего пользователя."""
        serializer = AvatarSerializer(request.user, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @avatar.mapping.delete
    def delete_avatar(self, request):
        """Удаляет аватар текущего пользователя."""
        user = request.user
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
        ).annotate(
            recipes_count=Count('recipes', distinct=True),
            is_subscribed=Value(True, output_field=BooleanField()),
        ).prefetch_related(
            Prefetch(
                'recipes',
                queryset=Recipe.objects.order_by('-pub_date'),
            ),
        ).order_by('id')
        pages = self.paginate_queryset(queryset)
        serializer = UserWithRecipesSerializer(
            pages,
            many=True,
            context={'request': request},
        )
        return self.get_paginated_response(serializer.data)

    @action(
        methods=('post',),
        detail=True,
        permission_classes=(IsAuthenticated,),
    )
    def subscribe(self, request, **kwargs):
        """Подписывает текущего пользователя на автора."""
        serializer = SubscriptionSerializer(
            data={'user': request.user.pk, 'author': self.get_object().pk},
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def unsubscribe(self, request, **kwargs):
        """Отписывает текущего пользователя от автора."""
        deleted, _ = Subscription.objects.filter(
            user=request.user,
            author=self.get_object(),
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


class RecipeViewSet(viewsets.ModelViewSet):
    """Рецепты, избранное, список покупок и короткие ссылки."""

    queryset = Recipe.objects.all()
    permission_classes = (IsAuthorOrReadOnly,)
    filterset_class = RecipeFilter
    http_method_names = ('get', 'post', 'patch', 'delete', 'head', 'options')

    def get_queryset(self):
        user = self.request.user
        false_value = Value(False, output_field=BooleanField())
        if user.is_authenticated:
            authors = User.objects.annotate(
                is_subscribed=Exists(
                    Subscription.objects.filter(
                        user=user,
                        author=OuterRef('pk'),
                    ),
                ),
            )
        else:
            authors = User.objects.annotate(is_subscribed=false_value)
        queryset = Recipe.objects.prefetch_related(
            Prefetch('author', queryset=authors),
            'tags',
            'recipe_ingredients__ingredient',
        ).distinct()
        if user.is_authenticated:
            return queryset.annotate(
                is_favorited=Exists(
                    Favorite.objects.filter(
                        user=user,
                        recipe=OuterRef('pk'),
                    ),
                ),
                is_in_shopping_cart=Exists(
                    ShoppingCart.objects.filter(
                        user=user,
                        recipe=OuterRef('pk'),
                    ),
                ),
            )
        return queryset.annotate(
            is_favorited=false_value,
            is_in_shopping_cart=false_value,
        )

    def get_serializer_class(self):
        if self.action in ('create', 'partial_update'):
            return RecipeWriteSerializer
        return RecipeReadSerializer

    def add_user_recipe(self, request, serializer_class):
        """Сохраняет связь пользователя с рецептом через сериализатор."""
        serializer = serializer_class(
            data={'user': request.user.pk, 'recipe': self.get_object().pk},
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete_user_recipe(self, request, model, error_absent):
        """Удаляет связь пользователя с рецептом."""
        deleted, _ = model.objects.filter(
            user=request.user,
            recipe=self.get_object(),
        ).delete()
        if not deleted:
            return Response(
                {'errors': error_absent},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=('post',),
        detail=True,
        permission_classes=(IsAuthenticated,),
    )
    def favorite(self, request, pk=None):
        """Добавляет рецепт в избранное."""
        return self.add_user_recipe(request, FavoriteSerializer)

    @favorite.mapping.delete
    def delete_favorite(self, request, pk=None):
        """Удаляет рецепт из избранного."""
        return self.delete_user_recipe(
            request,
            Favorite,
            'Рецепта нет в избранном.',
        )

    @action(
        methods=('post',),
        detail=True,
        permission_classes=(IsAuthenticated,),
    )
    def shopping_cart(self, request, pk=None):
        """Добавляет рецепт в список покупок."""
        return self.add_user_recipe(request, ShoppingCartSerializer)

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk=None):
        """Удаляет рецепт из списка покупок."""
        return self.delete_user_recipe(
            request,
            ShoppingCart,
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
