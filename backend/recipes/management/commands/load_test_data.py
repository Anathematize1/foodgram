from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from recipes.models import Ingredient, Recipe, RecipeIngredient, Tag
from users.models import User

PNG_1PX = (
    b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01'
    b'\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00'
    b'\x00\x0cIDATx\x9cc\xf8\xcf\xc0\x00\x00\x00\x03\x00\x01'
    b'\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82'
)


class Command(BaseCommand):
    """Создаёт тестовых пользователей, теги и рецепты."""

    help = 'Создаёт теги, пользователей и тестовые рецепты'

    def handle(self, *args, **options):
        tags = {
            'Завтрак': 'breakfast',
            'Обед': 'lunch',
            'Ужин': 'dinner',
        }
        tag_objects = []
        for name, slug in tags.items():
            tag, _ = Tag.objects.get_or_create(name=name, slug=slug)
            tag_objects.append(tag)

        users_data = (
            {
                'email': 'admin@foodgram.local',
                'username': 'admin',
                'first_name': 'Админ',
                'last_name': 'Проекта',
                'password': 'Admin123456',
                'is_staff': True,
                'is_superuser': True,
            },
            {
                'email': 'vasya@foodgram.local',
                'username': 'vasya',
                'first_name': 'Вася',
                'last_name': 'Пупкин',
                'password': 'Qwerty123',
            },
            {
                'email': 'petya@foodgram.local',
                'username': 'petya',
                'first_name': 'Петя',
                'last_name': 'Иванов',
                'password': 'Qwerty123',
            },
        )
        users = []
        for data in users_data:
            password = data.pop('password')
            user, created = User.objects.get_or_create(
                email=data['email'],
                defaults=data,
            )
            if created:
                user.set_password(password)
                user.save()
            users.append(user)

        ingredients = list(Ingredient.objects.all()[:6])
        if len(ingredients) < 2:
            self.stdout.write(
                self.style.WARNING(
                    'Сначала выполните: python manage.py load_ingredients',
                ),
            )
            return

        recipes_data = (
            (
                'Омлет',
                'Простой омлет на завтрак.',
                15,
                users[0],
                tag_objects[0],
            ),
            (
                'Борщ',
                'Классический борщ на обед.',
                90,
                users[1],
                tag_objects[1],
            ),
            (
                'Паста',
                'Паста на ужин.',
                25,
                users[2],
                tag_objects[2],
            ),
        )
        for name, text, time, author, tag in recipes_data:
            recipe, created = Recipe.objects.get_or_create(
                name=name,
                author=author,
                defaults={
                    'text': text,
                    'cooking_time': time,
                },
            )
            if created:
                recipe.image.save(
                    f'{recipe.short_code}.png',
                    ContentFile(PNG_1PX),
                    save=True,
                )
                recipe.tags.add(tag)
                RecipeIngredient.objects.create(
                    recipe=recipe,
                    ingredient=ingredients[0],
                    amount=2,
                )
                RecipeIngredient.objects.create(
                    recipe=recipe,
                    ingredient=ingredients[1],
                    amount=100,
                )
        self.stdout.write(self.style.SUCCESS('Тестовые данные загружены.'))
