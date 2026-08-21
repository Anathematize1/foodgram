"""Общие данные и хелперы для API-тестов."""
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient, APITestCase

from recipes.models import Ingredient, Recipe, RecipeIngredient, Tag
from users.models import User

IMAGE_PNG = (
    b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01'
    b'\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00'
    b'\x00\x0cIDATx\x9cc\xf8\xcf\xc0\x00\x00\x00\x03\x00\x01'
    b'\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82'
)

IMAGE_BASE64 = (
    'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABAgMAAABieywa'
    'AAAACVBMVEUAAAD///9fX1/S0ecCAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAACklEQV'
    'QImWNoAAAAggCByxOyYQAAAABJRU5ErkJggg=='
)


class BaseAPITestCase(APITestCase):
    """Базовый набор пользователей, тегов и ингредиентов."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='user@test.test',
            username='user',
            first_name='Иван',
            last_name='Иванов',
            password='Qwerty123',
        )
        self.other = User.objects.create_user(
            email='other@test.test',
            username='other',
            first_name='Пётр',
            last_name='Петров',
            password='Qwerty123',
        )
        self.tag_breakfast = Tag.objects.create(
            name='Завтрак',
            slug='breakfast',
        )
        self.tag_lunch = Tag.objects.create(name='Обед', slug='lunch')
        self.sugar = Ingredient.objects.create(
            name='Сахар',
            measurement_unit='г',
        )
        self.milk = Ingredient.objects.create(
            name='Молоко',
            measurement_unit='мл',
        )
        self.user_token = Token.objects.create(user=self.user)
        self.other_token = Token.objects.create(user=self.other)
        self.auth = APIClient()
        self.auth.credentials(
            HTTP_AUTHORIZATION=f'Token {self.user_token.key}',
        )
        self.other_client = APIClient()
        self.other_client.credentials(
            HTTP_AUTHORIZATION=f'Token {self.other_token.key}',
        )
        self.anon = APIClient()

    def make_recipe(self, author=None, name='Омлет', tags=None):
        recipe = Recipe.objects.create(
            author=author or self.user,
            name=name,
            text='Описание',
            cooking_time=10,
            image=SimpleUploadedFile('img.png', IMAGE_PNG, 'image/png'),
        )
        recipe.tags.set(tags or (self.tag_breakfast,))
        RecipeIngredient.objects.create(
            recipe=recipe,
            ingredient=self.sugar,
            amount=20,
        )
        return recipe

    def recipe_payload(self, **overrides):
        payload = {
            'ingredients': [
                {'id': self.sugar.id, 'amount': 10},
                {'id': self.milk.id, 'amount': 200},
            ],
            'tags': [self.tag_breakfast.id],
            'image': IMAGE_BASE64,
            'name': 'Сырники',
            'text': 'Приготовить',
            'cooking_time': 15,
        }
        payload.update(overrides)
        return payload
