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
    'blini.jpg': (
        'https://commons.wikimedia.org/wiki/Special:FilePath/'
        'Blin1.jpg?width=1280'
    ),
    'chicken_soup.jpg': (
        'https://commons.wikimedia.org/wiki/Special:FilePath/'
        'Chicken_noodle_soup_(1).jpg?width=1280'
    ),
    'buckwheat.jpg': (
        'https://commons.wikimedia.org/wiki/Special:FilePath/'
        'Boiled_buckwheat_groats.jpg?width=1280'
    ),
    'salmon.jpg': (
        'https://commons.wikimedia.org/wiki/Special:FilePath/'
        'Baked_salmon_with_dill_and_lemon.jpg?width=1280'
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
            {
                'name': 'Блины',
                'text': (
                    'Смешайте яйца, кефир, муку, сахар и соль до однородного '
                    'теста без комочков. Дайте постоять 10 минут. Жарьте '
                    'тонкие блины на разогретой сковороде со сливочным '
                    'маслом с двух сторон. Подавайте со сметаной.'
                ),
                'cooking_time': 30,
                'author': users[2],
                'tags': (tags['breakfast'],),
                'image': 'blini.jpg',
                'ingredients': (
                    ('яйца куриные', 100),
                    ('кефир', 300),
                    ('мука', 180),
                    ('сахар', 20),
                    ('соль', 3),
                    ('сливочное масло', 30),
                    ('сметана', 80),
                ),
            },
            {
                'name': 'Куриный суп',
                'text': (
                    'Отварите курицу в воде, снимите пену и выньте мясо. '
                    'В бульон положите нарезанный картофель, морковь и лук. '
                    'Добавьте рис и варите до готовности крупы. Верните '
                    'нарезанную курицу, посолите и посыпьте петрушкой.'
                ),
                'cooking_time': 50,
                'author': users[2],
                'tags': (tags['lunch'],),
                'image': 'chicken_soup.jpg',
                'ingredients': (
                    ('курица', 400),
                    ('вода', 1500),
                    ('картофель', 300),
                    ('морковь', 120),
                    ('лук репчатый', 80),
                    ('рис', 60),
                    ('петрушка', 10),
                    ('соль', 8),
                ),
            },
            {
                'name': 'Гречневая каша с грибами',
                'text': (
                    'Грибы и лук обжарьте на сливочном масле до золотистого '
                    'цвета. Гречневую крупу промойте, залейте водой, '
                    'добавьте соль и тушите под крышкой до мягкости. '
                    'Смешайте с грибами и сразу подавайте.'
                ),
                'cooking_time': 35,
                'author': users[2],
                'tags': (tags['dinner'],),
                'image': 'buckwheat.jpg',
                'ingredients': (
                    ('гречневая крупа', 200),
                    ('вода', 400),
                    ('грибы', 200),
                    ('лук репчатый', 80),
                    ('сливочное масло', 30),
                    ('соль', 5),
                ),
            },
            {
                'name': 'Запечённый лосось',
                'text': (
                    'Филе лосося посолите и поперчите, сбрызните лимонным '
                    'соком и оливковым маслом. Выложите на противень, '
                    'посыпьте укропом и запекайте при 180 °C около '
                    '20 минут. Подавайте с дольками лимона.'
                ),
                'cooking_time': 25,
                'author': users[2],
                'tags': (tags['dinner'],),
                'image': 'salmon.jpg',
                'ingredients': (
                    ('лосось филе', 400),
                    ('лимонный сок', 20),
                    ('оливковое масло', 20),
                    ('укроп', 10),
                    ('соль', 5),
                    ('перец черный молотый', 3),
                    ('лимоны', 50),
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
