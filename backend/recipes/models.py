from django.db import models

from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from django.contrib.auth.validators import UnicodeUsernameValidator


# Пользователь
class UserWithAvatar(AbstractUser):
    """
    Кастомная модель пользователя.
    """
    username = models.CharField(
        verbose_name='Юзернейм',
        unique=True,
        max_length=150,
        blank=False,
        null=False,
        validators=[UnicodeUsernameValidator()],
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
        max_length=254,
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
        ordering = ('username',)

    def __str__(self):
        return self.username


class Subscription(models.Model):
    """
    Модель подписки: связь между пользователем и автором рецептов.
    """
    # Кто подписывается
    user = models.ForeignKey(
        UserWithAvatar,
        verbose_name='Пользователь',
        related_name='subscriptions',
        on_delete=models.CASCADE
    )
    # На кого подписываются
    author = models.ForeignKey(
        UserWithAvatar,
        verbose_name='Автор рецептов',
        related_name='subscribing',
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


# Список избранного и покупок
class BaseList(models.Model):
    """
    Абстрактный базовый класс для избранного и списка покупок.
    """
    user = models.ForeignKey(
        UserWithAvatar,
        verbose_name='Пользователь',
        on_delete=models.CASCADE,
        related_name='in_%(class)ss'
    )
    recipe = models.ForeignKey(
        'Recipe',
        verbose_name='Рецепт',
        on_delete=models.CASCADE,
        related_name='in_%(class)ss',
    )

    class Meta:
        abstract = True
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_%(class)s'
            )
        ]

    def __str__(self):
        list = {
            'favorite': 'избранном',
            'shoppingcart': 'корзине',
        }.get(self.__class__.__name__.lower(), 'списке')
        return f'Рецепт {self.recipe.name} в {list} у {self.user.username}'


class Favorite(BaseList):
    """
    Модель списка избранного.
    """

    class Meta:
        verbose_name = 'избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'


class ShoppingCart(BaseList):
    """
    Модель списка покупок.
    """

    class Meta:
        verbose_name = 'список покупок'
        verbose_name_plural = 'Списки покупок'


# Ингредиент
class Ingredient(models.Model):
    """
    Модель ингредиента для рецептов.
    """
    name = models.CharField(
        verbose_name='Название',
        max_length=128,
        blank=False,
        null=False,
    )
    measurement_unit = models.CharField(
        verbose_name='Единица измерения',
        max_length=64,
        blank=False,
        null=False,
    )

    class Meta:
        verbose_name = 'ингредиент'
        verbose_name_plural = 'Ингредиенты'
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='unique_name_measurement_unit'
            )
        ]

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}.'


# Рецепты
class Recipe(models.Model):
    """
    Модель рецепта.
    """
    name = models.CharField(
        verbose_name='Название рецепта',
        max_length=256,
    )
    text = models.TextField(
        verbose_name='Описание рецепта',
    )
    cooking_time = models.IntegerField(
        verbose_name='Время приготовления в минутах',
        validators=(
            MinValueValidator(
                1,
                message='Время приготовления должно быть больше 0'
            ),
        )
    )
    image = models.ImageField(
        verbose_name='Картинка',
        upload_to='recipe_images/',
    )
    author = models.ForeignKey(
        UserWithAvatar,
        verbose_name='Автор рецепта',
        on_delete=models.CASCADE,
        related_name='user_recipes',
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        verbose_name='Ингредиенты',
        through='RecipeIngredient',
        related_name='recipes'
    )
    pub_date = models.DateTimeField(
        verbose_name='Дата добавления',
        auto_now_add=True
    )

    class Meta:
        verbose_name = 'рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-pub_date',)

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    """
    Вспомогательная модель.
    Хранит все ингредиенты всех рецептов.
    """
    recipe = models.ForeignKey(
        Recipe,
        verbose_name='Рецепт',
        on_delete=models.CASCADE,
        related_name='products'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        verbose_name='Продукт',
        on_delete=models.CASCADE,
        related_name='recipeingredients'
    )
    amount = models.IntegerField(
        verbose_name='Количество',
        validators=(
            MinValueValidator(
                1,
                message='Количество должно быть больше 0'
            ),
        )
    )

    class Meta:
        verbose_name = 'продукт для рецепта'
        verbose_name_plural = 'Продукты для рецепта'
        constraints = [
            models.UniqueConstraint(
                fields=('recipe', 'ingredient'),
                name='unique_recipe_ingredient'
            )
        ]

    def __str__(self):
        return (f'{self.recipe.name} содержит {self.ingredient.name} '
                f'в количестве {self.amount} {self.ingredient.measurement_unit}')
