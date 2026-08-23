"""Загрузка тегов, авторов и реальных рецептов с фотографиями."""
from urllib.request import Request, urlopen

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q

from recipes.models import Ingredient, Recipe, RecipeIngredient, Tag
from users.models import User

RECIPE_IMAGES = {
    'omelette.jpg': (
        'https://commons.wikimedia.org/wiki/Special:FilePath/'
        'Egg_omelette.JPG?width=1280'
    ),
    'borscht.jpg': (
        'https://commons.wikimedia.org/wiki/Special:FilePath/'
        'Borscht_served.jpg?width=1280'
    ),
    'carbonara.jpg': (
        'https://commons.wikimedia.org/wiki/Special:FilePath/'
        'Espaguetis_carbonara.jpg?width=1280'
    ),
    'syrniki.jpg': (
        'https://commons.wikimedia.org/wiki/Special:FilePath/'
        'Syrniki.jpg?width=1280'
    ),
    'greek_salad.jpg': (
        'https://commons.wikimedia.org/wiki/Special:FilePath/'
        'Horiatiki_salad.jpg?width=1280'
    ),
}


class Command(BaseCommand):
    """Создаёт теги, авторов и рецепты с фотографиями."""

    help = 'Создаёт теги, пользователей и рецепты с реальными фото'

    def handle(self, *args, **options):
        tags = self._create_tags()
        users = self._create_users()
        if not self._ingredients_ready():
            return
        self._create_recipes(tags, users)
        self.stdout.write(self.style.SUCCESS('Тестовые данные загружены.'))

    def _create_tags(self):
        tags = {}
        for name, slug in (
            ('Завтрак', 'breakfast'),
            ('Обед', 'lunch'),
            ('Ужин', 'dinner'),
        ):
            tag, _ = Tag.objects.get_or_create(name=name, slug=slug)
            tags[slug] = tag
        return tags

    def _create_users(self):
        users_data = (
            {
                'email': 'maria@foodgram.local',
                'username': 'maria',
                'first_name': 'Мария',
                'last_name': 'Ковалева',
                'password': 'Qwerty123',
            },
            {
                'email': 'ivan@foodgram.local',
                'username': 'ivan',
                'first_name': 'Иван',
                'last_name': 'Соколов',
                'password': 'Qwerty123',
            },
            {
                'email': 'olga@foodgram.local',
                'username': 'olga',
                'first_name': 'Ольга',
                'last_name': 'Морозова',
                'password': 'Qwerty123',
            },
        )
        users = []
        for data in users_data:
            password = data.pop('password')
            user = User.objects.filter(
                Q(email=data['email']) | Q(username=data['username']),
            ).first()
            if user is None:
                user = User.objects.create_user(password=password, **data)
            users.append(user)
        return users

    def _ingredients_ready(self):
        if Ingredient.objects.count() < 10:
            self.stdout.write(
                self.style.WARNING(
                    'Сначала выполните: python manage.py load_ingredients',
                ),
            )
            return False
        return True

    def _get_ingredient(self, name):
        ingredient = Ingredient.objects.filter(name=name).first()
        if ingredient is None:
            raise CommandError(f'Ингредиент не найден: {name}')
        return ingredient

    def _load_image(self, filename):
        candidates = (
            settings.BASE_DIR / 'data' / 'recipe_images' / filename,
            settings.BASE_DIR.parent / 'data' / 'recipe_images' / filename,
        )
        for local_path in candidates:
            if local_path.is_file():
                return ContentFile(local_path.read_bytes(), name=filename)
        url = RECIPE_IMAGES[filename]
        request = Request(url, headers={'User-Agent': 'Foodgram/1.0'})
        with urlopen(request, timeout=30) as response:
            return ContentFile(response.read(), name=filename)

    def _create_recipes(self, tags, users):
        recipes = (
            {
                'name': 'Омлет с сыром',
                'text': (
                    'Взбейте яйца с молоком и щепоткой соли. Разогрейте '
                    'сковородку с оливковым маслом, вылейте смесь и жарьте '
                    'на среднем огне 3–4 минуты. Посыпьте тёртым сыром, '
                    'сложите омлет пополам и сразу подавайте.'
                ),
                'cooking_time': 15,
                'author': users[0],
                'tags': (tags['breakfast'],),
                'image': 'omelette.jpg',
                'ingredients': (
                    ('яйца куриные', 120),
                    ('молоко', 50),
                    ('сыр твердый', 40),
                    ('соль', 3),
                    ('оливковое масло', 10),
                ),
            },
            {
                'name': 'Сырники',
                'text': (
                    'Смешайте творог, яйцо, сахар и муку до однородного '
                    'теста. Сформируйте небольшие лепёшки, обваляйте в муке '
                    'и обжарьте на оливковом масле с двух сторон до '
                    'золотистой корочки. Подавайте со сметаной.'
                ),
                'cooking_time': 25,
                'author': users[0],
                'tags': (tags['breakfast'],),
                'image': 'syrniki.jpg',
                'ingredients': (
                    ('творог', 400),
                    ('яйца куриные', 50),
                    ('сахар', 30),
                    ('мука', 60),
                    ('сметана', 80),
                    ('оливковое масло', 20),
                ),
            },
            {
                'name': 'Борщ',
                'text': (
                    'Отварите говядину до готовности и снимите пену. '
                    'Свеклу натрите, обжарьте с томатной пастой. Картофель, '
                    'капусту и лук добавьте в бульон, затем свеклу. '
                    'Варите до мягкости овощей, в конце положите чеснок и '
                    'укроп. Подавайте со сметаной.'
                ),
                'cooking_time': 90,
                'author': users[1],
                'tags': (tags['lunch'],),
                'image': 'borscht.jpg',
                'ingredients': (
                    ('говядина', 400),
                    ('свекла', 300),
                    ('капуста белокочанная', 250),
                    ('картофель', 300),
                    ('лук репчатый', 100),
                    ('томатная паста', 30),
                    ('чеснок', 10),
                    ('укроп', 10),
                    ('сметана', 80),
                    ('соль', 8),
                ),
            },
            {
                'name': 'Греческий салат',
                'text': (
                    'Крупно нарежьте помидоры, огурцы и лук. Добавьте '
                    'оливки и кубики феты. Заправьте оливковым маслом, '
                    'лимонным соком, солью и чёрным перцем. Аккуратно '
                    'перемешайте и сразу подавайте.'
                ),
                'cooking_time': 15,
                'author': users[2],
                'tags': (tags['lunch'],),
                'image': 'greek_salad.jpg',
                'ingredients': (
                    ('помидоры', 250),
                    ('огурцы', 200),
                    ('лук репчатый', 50),
                    ('оливки', 60),
                    ('фета', 120),
                    ('оливковое масло', 30),
                    ('лимонный сок', 15),
                    ('соль', 3),
                    ('перец черный молотый', 2),
                ),
            },
            {
                'name': 'Паста карбонара',
                'text': (
                    'Отварите спагетти в подсоленной воде до состояния '
                    'аль денте. Бекон обжарьте до хруста. Смешайте яйца '
                    'с тёртым сыром. Слейте пасту, сразу соедините с беконом '
                    'и яично-сырной смесью, активно перемешивая. Подавайте '
                    'с чёрным перцем.'
                ),
                'cooking_time': 25,
                'author': users[1],
                'tags': (tags['dinner'],),
                'image': 'carbonara.jpg',
                'ingredients': (
                    ('спагетти', 250),
                    ('бекон', 120),
                    ('яйца куриные', 100),
                    ('сыр твердый', 80),
                    ('соль', 5),
                    ('перец черный молотый', 3),
                ),
            },
        )
        for data in recipes:
            recipe, created = Recipe.objects.get_or_create(
                name=data['name'],
                author=data['author'],
                defaults={
                    'text': data['text'],
                    'cooking_time': data['cooking_time'],
                },
            )
            if not created:
                continue
            try:
                image = self._load_image(data['image'])
            except OSError as exc:
                recipe.delete()
                raise CommandError(
                    f'Не удалось загрузить фото {data["image"]}: {exc}',
                )
            recipe.image.save(data['image'], image, save=True)
            recipe.tags.set(data['tags'])
            for ingredient_name, amount in data['ingredients']:
                RecipeIngredient.objects.create(
                    recipe=recipe,
                    ingredient=self._get_ingredient(ingredient_name),
                    amount=amount,
                )
            self.stdout.write(f'Создан рецепт: {recipe.name}')
