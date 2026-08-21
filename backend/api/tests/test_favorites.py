from rest_framework import status

from recipes.models import Favorite

from .helpers import BaseAPITestCase


class FavoriteAPITests(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.recipe = self.make_recipe()

    def test_add_and_delete(self):
        url = f'/api/recipes/{self.recipe.id}/favorite/'
        created = self.auth.post(url)
        self.assertEqual(created.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            Favorite.objects.filter(
                user=self.user,
                recipe=self.recipe,
            ).exists()
        )
        duplicate = self.auth.post(url)
        self.assertEqual(duplicate.status_code, status.HTTP_400_BAD_REQUEST)
        deleted = self.auth.delete(url)
        self.assertEqual(deleted.status_code, status.HTTP_204_NO_CONTENT)
        again = self.auth.delete(url)
        self.assertEqual(again.status_code, status.HTTP_400_BAD_REQUEST)

    def test_anonymous_and_missing(self):
        url = f'/api/recipes/{self.recipe.id}/favorite/'
        anon = self.anon.post(url)
        self.assertEqual(anon.status_code, status.HTTP_401_UNAUTHORIZED)
        missing = self.auth.post('/api/recipes/99999/favorite/')
        self.assertEqual(missing.status_code, status.HTTP_404_NOT_FOUND)
