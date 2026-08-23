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
            default=self._default_csv_path(),
        )

    @staticmethod
    def _default_csv_path():
        candidates = (
            settings.BASE_DIR / 'data' / 'ingredients.csv',
            settings.BASE_DIR.parent / 'data' / 'ingredients.csv',
        )
        for candidate in candidates:
            if candidate.exists():
                return str(candidate)
        return str(candidates[0])

    def handle(self, *args, **options):
        path = Path(options['path'])
        if not path.exists():
            raise CommandError(f'Файл не найден: {path}')

        ingredients = []
        skipped = 0
        with path.open(encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            for line_number, row in enumerate(reader, start=1):
                if len(row) != 2:
                    skipped += 1
                    self.stderr.write(
                        f'Строка {line_number}: пропущена, '
                        'ожидалось 2 колонки.',
                    )
                    continue
                name, measurement_unit = (item.strip() for item in row)
                if not name or not measurement_unit:
                    skipped += 1
                    self.stderr.write(
                        f'Строка {line_number}: пропущена, пустые значения.',
                    )
                    continue
                ingredients.append(
                    Ingredient(name=name, measurement_unit=measurement_unit),
                )

        before = Ingredient.objects.count()
        Ingredient.objects.bulk_create(
            ingredients,
            ignore_conflicts=True,
        )
        created_count = Ingredient.objects.count() - before
        self.stdout.write(
            self.style.SUCCESS(
                f'Обработано строк: {len(ingredients)}. '
                f'Создано новых: {created_count}. '
                f'Пропущено: {skipped}.',
            ),
        )
