"""Сборка текстового списка покупок."""
from django.db.models import Sum

from recipes.models import RecipeIngredient


def get_shopping_list_text(user):
    """Возвращает суммированный список ингредиентов пользователя."""
    ingredients = (
        RecipeIngredient.objects.filter(
            recipe__in_shopping_cart__user=user,
        )
        .values(
            'ingredient__name',
            'ingredient__measurement_unit',
        )
        .annotate(total=Sum('amount'))
        .order_by('ingredient__name')
    )
    lines = ['Список покупок:\n']
    for item in ingredients:
        name = item['ingredient__name']
        unit = item['ingredient__measurement_unit']
        lines.append(f'{name} ({unit}) — {item["total"]}')
    return '\n'.join(lines)
