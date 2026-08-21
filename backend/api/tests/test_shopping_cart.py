from rest_framework import status

from recipes.models import RecipeIngredient, ShoppingCart

from .helpers import BaseAPITestCase


class ShoppingCartAPITests(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.recipe = self.make_recipe()

    def test_add_and_delete(self):
        url = f'/api/recipes/{self.recipe.id}/shopping_cart/'
        created = self.auth.post(url)
        self.assertEqual(created.status_code, status.HTTP_201_CREATED)
        duplicate = self.auth.post(url)
        self.assertEqual(duplicate.status_code, status.HTTP_400_BAD_REQUEST)
        deleted = self.auth.delete(url)
        self.assertEqual(deleted.status_code, status.HTTP_204_NO_CONTENT)
        again = self.auth.delete(url)
        self.assertEqual(again.status_code, status.HTTP_400_BAD_REQUEST)

    def test_anonymous_and_missing(self):
        url = f'/api/recipes/{self.recipe.id}/shopping_cart/'
        anon = self.anon.post(url)
        self.assertEqual(anon.status_code, status.HTTP_401_UNAUTHORIZED)
        missing = self.auth.post('/api/recipes/99999/shopping_cart/')
        self.assertEqual(missing.status_code, status.HTTP_404_NOT_FOUND)

    def test_download_aggregates_ingredients(self):
        second = self.make_recipe(name='Каша')
        RecipeIngredient.objects.filter(recipe=second).update(amount=30)
        ShoppingCart.objects.create(user=self.user, recipe=self.recipe)
        ShoppingCart.objects.create(user=self.user, recipe=second)
        response = self.auth.get('/api/recipes/download_shopping_cart/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        body = response.content.decode('utf-8')
        self.assertIn('Сахар (г) — 50', body)
        self.assertEqual(body.count('Сахар'), 1)
