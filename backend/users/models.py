from django.db import models
from django.contrib.auth.models import AbstractUser


class CustomUser(AbstractUser):
    """
    Кастомная модель пользователя.
    """
    username = models.CharField(
        verbose_name='Юзернейм',
        unique=True,
        max_length=150,
        blank=False,
        null=False,
    )
    first_name = models.CharField(
        verbose_name='Имя',
        max_length=150,
        blank=False,
        null=False,
    )
    last_name = models.CharField(
        verbose_name='Фамилия',
        max_length=150,
        blank=False,
        null=False,
    )
    email = models.EmailField(
        verbose_name='Адрес электронной почты',
        unique=True,
        blank=False,
        null=False,
    )
    avatar = models.ImageField(
        verbose_name='Аватар',
        upload_to='avatars/',
        default='avatars/default.png',
        blank=True,
        null=True,
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        verbose_name = 'пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username


class Subscription(models.Model):
    """
    Модель подписки: связь между пользователем и автором рецептов.
    """
    # Кто подписывается
    user = models.ForeignKey(
        CustomUser,
        verbose_name='Пользователь',
        related_name='subscriptions',
        on_delete=models.CASCADE
    )
    # На кого подписываются
    author = models.ForeignKey(
        CustomUser,
        verbose_name='Автор рецептов',
        related_name='subscribers',
        on_delete=models.CASCADE
    )

    class Meta:
        verbose_name = 'подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_user_author'
            )
        ]

    def __str__(self):
        return f'{self.user.username} подписан на {self.author.username}'

    @classmethod
    def is_subscribed(cls, user, author):
        """
        Проверка: подписан ли пользователь на автора.
        """
        if not user or not user.is_authenticated:
            return False
        return cls.objects.filter(user=user, author=author).exists()
