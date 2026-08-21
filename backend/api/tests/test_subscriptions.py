from rest_framework import status

from .helpers import BaseAPITestCase


class SubscriptionAPITests(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.make_recipe(author=self.other, name='Первый')
        self.make_recipe(author=self.other, name='Второй')
        self.make_recipe(author=self.other, name='Третий')

    def test_subscribe_and_unsubscribe(self):
        url = f'/api/users/{self.other.id}/subscribe/'
        created = self.auth.post(url)
        self.assertEqual(created.status_code, status.HTTP_201_CREATED)
        self.assertTrue(created.data['is_subscribed'])
        duplicate = self.auth.post(url)
        self.assertEqual(duplicate.status_code, status.HTTP_400_BAD_REQUEST)
        deleted = self.auth.delete(url)
        self.assertEqual(deleted.status_code, status.HTTP_204_NO_CONTENT)
        again = self.auth.delete(url)
        self.assertEqual(again.status_code, status.HTTP_400_BAD_REQUEST)

    def test_self_subscribe_and_anonymous(self):
        self_url = f'/api/users/{self.user.id}/subscribe/'
        self_sub = self.auth.post(self_url)
        self.assertEqual(self_sub.status_code, status.HTTP_400_BAD_REQUEST)
        anon = self.anon.post(f'/api/users/{self.other.id}/subscribe/')
        self.assertEqual(anon.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_pagination_and_recipes_limit(self):
        self.auth.post(f'/api/users/{self.other.id}/subscribe/')
        listing = self.auth.get('/api/users/subscriptions/?limit=1')
        self.assertEqual(listing.status_code, status.HTTP_200_OK)
        self.assertEqual(listing.data['count'], 1)
        limited = self.auth.get(
            '/api/users/subscriptions/?recipes_limit=2',
        )
        recipes = limited.data['results'][0]['recipes']
        self.assertEqual(len(recipes), 2)
        self.assertEqual(limited.data['results'][0]['recipes_count'], 3)
