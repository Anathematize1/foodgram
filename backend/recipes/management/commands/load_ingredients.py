import csv
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from recipes.models import Ingredient


class Command(BaseCommand):
    """Загружает ингредиенты из CSV."""

    help = 'Загружает ингредиенты из CSV-файла data/ingredients.csv'

    def add_arguments(self, parser):
        parser.add_argument(
            'path',
            nargs='?',
            type=str,
            default=str(settings.BASE_DIR.parent / 'data' / 'ingredients.csv'),
        )

    def handle(self, *args, **options):
        path = Path(options['path'])
        if not path.exists():
            raise CommandError(f'Файл не найден: {path}')

        ingredients = []
        with path.open(encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                if len(row) != 2:
                    continue
                name, measurement_unit = row
                ingredients.append(
                    Ingredient(name=name, measurement_unit=measurement_unit),
                )

        created = Ingredient.objects.bulk_create(
            ingredients,
            ignore_conflicts=True,
        )
        self.stdout.write(
            self.style.SUCCESS(f'Загружено ингредиентов: {len(created)}'),
        )
