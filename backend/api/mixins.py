"""Миксины для повторяющихся действий API."""
from rest_framework import status
from rest_framework.response import Response

from .serializers import RecipeMinifiedSerializer


class AddDeleteRecipeMixin:
    """Добавление и удаление связи пользователя с рецептом."""

    def add_delete_recipe(self, request, model, error_exists, error_absent):
        """Создаёт или удаляет запись связи user-recipe."""
        recipe = self.get_object()
        relation = model.objects.filter(user=request.user, recipe=recipe)
        if request.method == 'POST':
            if relation.exists():
                return Response(
                    {'errors': error_exists},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            model.objects.create(user=request.user, recipe=recipe)
            serializer = RecipeMinifiedSerializer(
                recipe,
                context={'request': request},
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if not relation.exists():
            return Response(
                {'errors': error_absent},
                status=status.HTTP_400_BAD_REQUEST,
            )
        relation.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
