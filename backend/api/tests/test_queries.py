from django.db import connection
from django.test.utils import CaptureQueriesContext

from .helpers import BaseAPITestCase


class RecipeQueryTests(BaseAPITestCase):
    def test_recipe_list_query_count_does_not_grow(self):
        for index in range(3):
            self.make_recipe(name=f'Рецепт {index}')
        with CaptureQueriesContext(connection) as first:
            response = self.auth.get('/api/recipes/')
        self.assertEqual(response.status_code, 200)
        baseline = len(first)
        for index in range(8):
            self.make_recipe(name=f'Ещё {index}')
        with CaptureQueriesContext(connection) as second:
            response = self.auth.get('/api/recipes/?limit=6')
        self.assertEqual(response.status_code, 200)
        self.assertLessEqual(len(second), baseline + 2)
