"""Сериализаторы API Foodgram."""
from django.db import transaction
from djoser.serializers import UserCreateSerializer as DjoserUserCreate
from djoser.serializers import UserSerializer as DjoserUserSerializer
from rest_framework import serializers

from recipes.constants import MIN_AMOUNT, MIN_COOKING_TIME
from recipes.models import Ingredient, Recipe, RecipeIngredient, Tag
from users.models import User

from .fields import Base64ImageField


class UserCreateSerializer(DjoserUserCreate):
    """Сериализатор регистрации пользователя."""

    class Meta(DjoserUserCreate.Meta):
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'password',
        )
        extra_kwargs = {'password': {'write_only': True}}


class UserSerializer(DjoserUserSerializer):
    """Сериализатор пользователя с флагом подписки."""

    is_subscribed = serializers.SerializerMethodField()
    avatar = Base64ImageField(required=False, allow_null=True)

    class Meta(DjoserUserSerializer.Meta):
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
        if not request or request.user.is_anonymous:
            return False
        if obj.pk == request.user.pk:
            return False
        if hasattr(obj, 'is_subscribed_ann'):
            return bool(obj.is_subscribed_ann)
        subscribed_ids = self.context.get('subscribed_ids')
        if subscribed_ids is not None:
            return obj.pk in subscribed_ids
        return False


class AvatarSerializer(serializers.ModelSerializer):
    """Сериализатор загрузки и отдачи аватара."""

    avatar = Base64ImageField(required=True, allow_null=False)

    class Meta:
        model = User
        fields = ('avatar',)


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор тега."""

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор ингредиента."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    """Ингредиент в составе рецепта при чтении."""

    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit',
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class IngredientWriteSerializer(serializers.Serializer):
    """Ингредиент и количество при создании или изменении рецепта."""

    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
    )
    amount = serializers.IntegerField(min_value=MIN_AMOUNT)


class RecipeMinifiedSerializer(serializers.ModelSerializer):
    """Краткое представление рецепта."""

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class UserWithRecipesSerializer(UserSerializer):
    """Пользователь со списком своих рецептов."""

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(read_only=True)

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ('recipes', 'recipes_count')

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes = obj.recipes.all()
        if request:
            limit = request.query_params.get('recipes_limit')
            if limit and limit.isdigit():
                recipes = recipes[:int(limit)]
        return RecipeMinifiedSerializer(
            recipes,
            many=True,
            context=self.context,
        ).data


class RecipeReadSerializer(serializers.ModelSerializer):
    """Сериализатор рецепта для чтения."""

    tags = TagSerializer(many=True, read_only=True)
    author = UserSerializer(read_only=True)
    ingredients = IngredientInRecipeSerializer(
        source='recipe_ingredients',
        many=True,
        read_only=True,
    )
    is_favorited = serializers.BooleanField(
        read_only=True,
        source='is_favorited_ann',
    )
    is_in_shopping_cart = serializers.BooleanField(
        read_only=True,
        source='is_in_shopping_cart_ann',
    )

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )


class RecipeWriteSerializer(serializers.ModelSerializer):
    """Сериализатор создания и обновления рецепта."""

    ingredients = IngredientWriteSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
    )
    image = Base64ImageField()
    cooking_time = serializers.IntegerField(min_value=MIN_COOKING_TIME)

    class Meta:
        model = Recipe
        fields = (
            'ingredients',
            'tags',
            'image',
            'name',
            'text',
            'cooking_time',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance is not None:
            self.fields['image'].required = False

    def validate(self, data):
        ingredients = data.get('ingredients')
        tags = data.get('tags')
        if not ingredients:
            raise serializers.ValidationError(
                {'ingredients': 'Нужен хотя бы один ингредиент.'},
            )
        if not tags:
            raise serializers.ValidationError(
                {'tags': 'Нужен хотя бы один тег.'},
            )
        ingredient_ids = [item['id'] for item in ingredients]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError(
                {'ingredients': 'Ингредиенты не должны повторяться.'},
            )
        if len(tags) != len(set(tags)):
            raise serializers.ValidationError(
                {'tags': 'Теги не должны повторяться.'},
            )
        return data

    @staticmethod
    def set_ingredients(recipe, ingredients):
        RecipeIngredient.objects.bulk_create(
            RecipeIngredient(
                recipe=recipe,
                ingredient=item['id'],
                amount=item['amount'],
            )
            for item in ingredients
        )

    @transaction.atomic
    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(
            author=self.context['request'].user,
            **validated_data,
        )
        recipe.tags.set(tags)
        self.set_ingredients(recipe, ingredients)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        instance.tags.set(tags)
        instance.recipe_ingredients.all().delete()
        self.set_ingredients(instance, ingredients)
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        user = self.context['request'].user
        if user.is_authenticated:
            instance.is_favorited_ann = user.favorites.filter(
                recipe=instance,
            ).exists()
            instance.is_in_shopping_cart_ann = user.shopping_cart.filter(
                recipe=instance,
            ).exists()
        else:
            instance.is_favorited_ann = False
            instance.is_in_shopping_cart_ann = False
        return RecipeReadSerializer(instance, context=self.context).data
