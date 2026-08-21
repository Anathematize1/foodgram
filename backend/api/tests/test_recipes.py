from rest_framework import status

from recipes.models import Recipe

from .helpers import BaseAPITestCase


class RecipeAPITests(BaseAPITestCase):
    def test_create_recipe(self):
        response = self.auth.post(
            '/api/recipes/',
            self.recipe_payload(),
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Recipe.objects.count(), 1)
        self.assertEqual(len(response.data['ingredients']), 2)

    def test_create_anonymous(self):
        response = self.anon.post(
            '/api/recipes/',
            self.recipe_payload(),
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_and_detail(self):
        recipe = self.make_recipe()
        listing = self.anon.get('/api/recipes/')
        self.assertEqual(listing.status_code, status.HTTP_200_OK)
        self.assertEqual(listing.data['count'], 1)
        detail = self.anon.get(f'/api/recipes/{recipe.id}/')
        self.assertEqual(detail.status_code, status.HTTP_200_OK)
        self.assertEqual(detail.data['name'], recipe.name)

    def test_patch_own_recipe(self):
        recipe = self.make_recipe()
        payload = self.recipe_payload(name='Новое имя')
        payload.pop('image')
        response = self.auth.patch(
            f'/api/recipes/{recipe.id}/',
            payload,
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        self.assertEqual(recipe.name, 'Новое имя')

    def test_patch_foreign_recipe(self):
        recipe = self.make_recipe(author=self.other)
        payload = self.recipe_payload(name='Хаки')
        payload.pop('image')
        response = self.auth.patch(
            f'/api/recipes/{recipe.id}/',
            payload,
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_own_and_foreign(self):
        own = self.make_recipe()
        foreign = self.make_recipe(author=self.other, name='Чужой')
        forbidden = self.auth.delete(f'/api/recipes/{foreign.id}/')
        self.assertEqual(forbidden.status_code, status.HTTP_403_FORBIDDEN)
        deleted = self.auth.delete(f'/api/recipes/{own.id}/')
        self.assertEqual(deleted.status_code, status.HTTP_204_NO_CONTENT)
        anon = self.anon.delete(f'/api/recipes/{foreign.id}/')
        self.assertEqual(anon.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_invalid_ingredients_and_tags(self):
        empty = self.auth.post(
            '/api/recipes/',
            self.recipe_payload(ingredients=[]),
            format='json',
        )
        self.assertEqual(empty.status_code, status.HTTP_400_BAD_REQUEST)
        duplicate = self.auth.post(
            '/api/recipes/',
            self.recipe_payload(
                ingredients=[
                    {'id': self.sugar.id, 'amount': 1},
                    {'id': self.sugar.id, 'amount': 2},
                ],
            ),
            format='json',
        )
        self.assertEqual(duplicate.status_code, status.HTTP_400_BAD_REQUEST)
        missing = self.auth.post(
            '/api/recipes/',
            self.recipe_payload(
                ingredients=[{'id': 99999, 'amount': 1}],
            ),
            format='json',
        )
        self.assertEqual(missing.status_code, status.HTTP_400_BAD_REQUEST)
        no_tags = self.auth.post(
            '/api/recipes/',
            self.recipe_payload(tags=[]),
            format='json',
        )
        self.assertEqual(no_tags.status_code, status.HTTP_400_BAD_REQUEST)
        dup_tags = self.auth.post(
            '/api/recipes/',
            self.recipe_payload(
                tags=[self.tag_breakfast.id, self.tag_breakfast.id],
            ),
            format='json',
        )
        self.assertEqual(dup_tags.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_cooking_time_and_amount(self):
        time = self.auth.post(
            '/api/recipes/',
            self.recipe_payload(cooking_time=0),
            format='json',
        )
        self.assertEqual(time.status_code, status.HTTP_400_BAD_REQUEST)
        amount = self.auth.post(
            '/api/recipes/',
            self.recipe_payload(
                ingredients=[{'id': self.sugar.id, 'amount': 0}],
            ),
            format='json',
        )
        self.assertEqual(amount.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_replaces_ingredients(self):
        recipe = self.make_recipe()
        payload = self.recipe_payload(
            ingredients=[{'id': self.milk.id, 'amount': 50}],
        )
        payload.pop('image')
        response = self.auth.patch(
            f'/api/recipes/{recipe.id}/',
            payload,
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.recipe_ingredients.count(), 1)
        self.assertEqual(
            recipe.recipe_ingredients.first().ingredient,
            self.milk,
        )
