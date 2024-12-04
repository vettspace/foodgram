from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Кастомная модель пользователя, расширяющая стандартную модель AbstractUser.

    Поля:
        email (EmailField): Уникальный адрес электронной почты пользователя.
        first_name (CharField): Имя пользователя.
        last_name (CharField): Фамилия пользователя.

    Атрибуты:
        USERNAME_FIELD (str): Поле для идентификации пользователя.
        REQUIRED_FIELDS (list): Обязательные поля при создании пользователя.
    """

    email = models.EmailField(
        'Email',
        max_length=200,
        unique=True,
    )
    first_name = models.CharField('Имя', max_length=150)
    last_name = models.CharField('Фамилия', max_length=150)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('id',)

    def __str__(self):
        """
        Возвращает строковое представление пользователя.
        """
        return self.email
