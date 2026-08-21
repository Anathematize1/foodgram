"""Модели пользователей и подписок."""
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models

from .constants import MAX_EMAIL, MAX_NAME, MAX_USERNAME


class User(AbstractUser):
    """Пользователь с авторизацией по email."""

    username = models.CharField(
        'Уникальный юзернейм',
        max_length=MAX_USERNAME,
        unique=True,
        validators=(UnicodeUsernameValidator(),),
    )
    email = models.EmailField(
        'Адрес электронной почты',
        max_length=MAX_EMAIL,
        unique=True,
    )
    first_name = models.CharField('Имя', max_length=MAX_NAME)
    last_name = models.CharField('Фамилия', max_length=MAX_NAME)
    avatar = models.ImageField(
        'Аватар',
        upload_to='users/avatars/',
        blank=True,
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ('username', 'first_name', 'last_name')

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('id',)

    def __str__(self):
        return self.username


class Subscription(models.Model):
    """Подписка пользователя на автора рецептов."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name='Подписчик',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscribers',
        verbose_name='Автор',
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'author'),
                name='unique_subscription',
            ),
            models.CheckConstraint(
                condition=~models.Q(user=models.F('author')),
                name='prevent_self_subscription',
            ),
        )

    def __str__(self):
        return f'{self.user} подписан на {self.author}'
