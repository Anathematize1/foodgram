from rest_framework import status

from .helpers import IMAGE_BASE64, BaseAPITestCase


class UserAPITests(BaseAPITestCase):
    def test_registration(self):
        response = self.anon.post(
            '/api/users/',
            {
                'email': 'new@test.test',
                'username': 'newbie',
                'first_name': 'Новый',
                'last_name': 'Пользователь',
                'password': 'VeryStr0ngPass99',
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNotIn('password', response.data)

    def test_duplicate_email(self):
        response = self.anon.post(
            '/api/users/',
            {
                'email': self.user.email,
                'username': 'another',
                'first_name': 'А',
                'last_name': 'Б',
                'password': 'Qwerty123',
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_duplicate_username(self):
        response = self.anon.post(
            '/api/users/',
            {
                'email': 'uniq@test.test',
                'username': self.user.username,
                'first_name': 'А',
                'last_name': 'Б',
                'password': 'Qwerty123',
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_and_me(self):
        login = self.anon.post(
            '/api/auth/token/login/',
            {'email': self.user.email, 'password': 'Qwerty123'},
            format='json',
        )
        self.assertEqual(login.status_code, status.HTTP_200_OK)
        self.assertIn('auth_token', login.data)
        me = self.auth.get('/api/users/me/')
        self.assertEqual(me.status_code, status.HTTP_200_OK)
        self.assertFalse(me.data['is_subscribed'])

    def test_me_anonymous(self):
        response = self.anon.get('/api/users/me/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_users_pagination(self):
        response = self.anon.get('/api/users/?limit=1')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertIn('count', response.data)

    def test_set_password(self):
        response = self.auth.post(
            '/api/users/set_password/',
            {
                'current_password': 'Qwerty123',
                'new_password': 'NewPass123',
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_avatar_put_and_delete(self):
        put = self.auth.put(
            '/api/users/me/avatar/',
            {'avatar': IMAGE_BASE64},
            format='json',
        )
        self.assertEqual(put.status_code, status.HTTP_200_OK)
        self.assertIn('avatar', put.data)
        delete = self.auth.delete('/api/users/me/avatar/')
        self.assertEqual(delete.status_code, status.HTTP_204_NO_CONTENT)

    def test_avatar_anonymous(self):
        response = self.anon.put(
            '/api/users/me/avatar/',
            {'avatar': IMAGE_BASE64},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
