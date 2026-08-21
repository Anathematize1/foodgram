from rest_framework import status

from recipes.models import Favorite, ShoppingCart

from .helpers import BaseAPITestCase


class RecipeFilterTests(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.fav = self.make_recipe(name='Избранный')
        self.cart = self.make_recipe(name='В корзине')
        self.plain = self.make_recipe(
            name='Обычный',
            tags=(self.tag_lunch,),
        )
        Favorite.objects.create(user=self.user, recipe=self.fav)
        ShoppingCart.objects.create(user=self.user, recipe=self.cart)

    def test_is_favorited_true_false(self):
        true_resp = self.auth.get('/api/recipes/?is_favorited=true')
        self.assertEqual(true_resp.status_code, status.HTTP_200_OK)
        ids = [item['id'] for item in true_resp.data['results']]
        self.assertEqual(ids, [self.fav.id])
        false_resp = self.auth.get('/api/recipes/?is_favorited=false')
        false_ids = [item['id'] for item in false_resp.data['results']]
        self.assertNotIn(self.fav.id, false_ids)
        self.assertIn(self.plain.id, false_ids)

    def test_is_in_shopping_cart_true_false(self):
        true_resp = self.auth.get('/api/recipes/?is_in_shopping_cart=true')
        ids = [item['id'] for item in true_resp.data['results']]
        self.assertEqual(ids, [self.cart.id])
        false_resp = self.auth.get(
            '/api/recipes/?is_in_shopping_cart=false',
        )
        false_ids = [item['id'] for item in false_resp.data['results']]
        self.assertNotIn(self.cart.id, false_ids)

    def test_anonymous_favorited_true_is_empty(self):
        response = self.anon.get('/api/recipes/?is_favorited=true')
        self.assertEqual(response.data['count'], 0)

    def test_tags_and_author(self):
        tags = self.anon.get('/api/recipes/?tags=lunch')
        ids = [item['id'] for item in tags.data['results']]
        self.assertEqual(ids, [self.plain.id])
        author = self.anon.get(f'/api/recipes/?author={self.user.id}')
        self.assertEqual(author.data['count'], 3)
