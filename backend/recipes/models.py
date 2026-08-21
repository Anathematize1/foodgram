"""Модели рецептов, тегов, ингредиентов и связанных сущностей."""
import secrets
import string

from django.core.validators import MinValueValidator
from django.db import models

from users.models import User

from .constants import (
    MAX_INGREDIENT_NAME,
    MAX_MEASUREMENT_UNIT,
    MAX_RECIPE_NAME,
    MAX_TAG_NAME,
    MAX_TAG_SLUG,
    MIN_AMOUNT,
    MIN_COOKING_TIME,
    SHORT_CODE_LENGTH,
)

ALPHABET = string.ascii_letters + string.digits


def generate_short_code():
    """Возвращает случайный код для короткой ссылки на рецепт."""
    return ''.join(
        secrets.choice(ALPHABET) for _ in range(SHORT_CODE_LENGTH)
    )


class Tag(models.Model):
    """Тег для классификации рецептов."""

    name = models.CharField(
        'Название',
        max_length=MAX_TAG_NAME,
        unique=True,
    )
    slug = models.SlugField(
        'Слаг',
        max_length=MAX_TAG_SLUG,
        unique=True,
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ('name',)

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Ингредиент с единицей измерения."""

    name = models.CharField(
        'Название',
        max_length=MAX_INGREDIENT_NAME,
        db_index=True,
    )
    measurement_unit = models.CharField(
        'Единица измерения',
        max_length=MAX_MEASUREMENT_UNIT,
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ('name',)
        constraints = (
            models.UniqueConstraint(
                fields=('name', 'measurement_unit'),
                name='unique_ingredient',
            ),
        )

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'


class Recipe(models.Model):
    """Рецепт со списком ингредиентов и тегов."""

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор',
    )
    name = models.CharField('Название', max_length=MAX_RECIPE_NAME)
    image = models.ImageField('Картинка', upload_to='recipes/images/')
    text = models.TextField('Описание')
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        related_name='recipes',
        verbose_name='Ингредиенты',
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='recipes',
        verbose_name='Теги',
    )
    cooking_time = models.PositiveSmallIntegerField(
        'Время приготовления (в минутах)',
        validators=(MinValueValidator(MIN_COOKING_TIME),),
    )
    pub_date = models.DateTimeField(
        'Дата публикации',
        auto_now_add=True,
        db_index=True,
    )
    short_code = models.CharField(
        'Код короткой ссылки',
        max_length=SHORT_CODE_LENGTH,
        unique=True,
        db_index=True,
        editable=False,
        default=generate_short_code,
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-pub_date',)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.short_code:
            code = generate_short_code()
            while Recipe.objects.filter(short_code=code).exists():
                code = generate_short_code()
            self.short_code = code
        super().save(*args, **kwargs)


class RecipeIngredient(models.Model):
    """Количество ингредиента в конкретном рецепте."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',
        verbose_name='Рецепт',
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',
        verbose_name='Ингредиент',
    )
    amount = models.PositiveSmallIntegerField(
        'Количество',
        validators=(MinValueValidator(MIN_AMOUNT),),
    )

    class Meta:
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецептах'
        constraints = (
            models.UniqueConstraint(
                fields=('recipe', 'ingredient'),
                name='unique_recipe_ingredient',
            ),
        )

    def __str__(self):
        return f'{self.ingredient} в {self.recipe}'


class UserRecipeRelation(models.Model):
    """Абстрактная связь пользователя с рецептом."""

    class Meta:
        abstract = True

    def __str__(self):
        return f'{self.user} — {self.recipe}'


class Favorite(UserRecipeRelation):
    """Рецепт в избранном пользователя."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Рецепт',
    )

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_favorite',
            ),
        )


class ShoppingCart(UserRecipeRelation):
    """Рецепт в списке покупок пользователя."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='in_shopping_cart',
        verbose_name='Рецепт',
    )

    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_shopping_cart',
            ),
        )
