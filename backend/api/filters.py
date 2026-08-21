"""Фильтры для ингредиентов и рецептов."""
from django_filters.rest_framework import FilterSet, filters

from recipes.models import Ingredient, Recipe, Tag


class IngredientFilter(FilterSet):
    """Поиск ингредиента по началу названия без учёта регистра."""

    name = filters.CharFilter(method='filter_name')

    class Meta:
        model = Ingredient
        fields = ('name',)

    def filter_name(self, queryset, name, value):
        return queryset.filter(name__istartswith=value)


class RecipeFilter(FilterSet):
    """Фильтрация рецептов по тегам, автору, избранному и корзине."""

    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all(),
    )
    is_favorited = filters.BooleanFilter(method='filter_is_favorited')
    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_is_in_shopping_cart',
    )

    class Meta:
        model = Recipe
        fields = ('author', 'tags', 'is_favorited', 'is_in_shopping_cart')

    def filter_is_favorited(self, queryset, name, value):
        return self._filter_user_flag(
            queryset,
            value,
            'is_favorited_ann',
        )

    def filter_is_in_shopping_cart(self, queryset, name, value):
        return self._filter_user_flag(
            queryset,
            value,
            'is_in_shopping_cart_ann',
        )

    def _filter_user_flag(self, queryset, value, annotation):
        if self.request.user.is_anonymous:
            if value:
                return queryset.none()
            return queryset
        return queryset.filter(**{annotation: bool(value)})
