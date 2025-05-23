from django.db import models

from users.models import CustomUser
from ingredients.models import Ingredient


class Recipe(models.Model):
    """
    Модель рецепта.
    """
    name = models.CharField(
        verbose_name='Название рецепта',
        max_length=256,
        blank=False,
        null=False,
    )
    text = models.TextField(
        verbose_name='Описание рецепта',
        blank=False,
        null=False,
    )
    cooking_time = models.IntegerField(
        verbose_name='Время приготовления в минутах',
        blank=False,
        null=False,
    )
    image = models.ImageField(
        verbose_name='Картинка',
        upload_to='recipe_images/',
        blank=False,
        null=False,
    )
    author = models.ForeignKey(
        CustomUser,
        verbose_name='Автор рецепта',
        on_delete=models.CASCADE,
        blank=False,
        null=False,
        related_name='recipes',
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        verbose_name='Ингредиенты',
        through='RecipeIngredient',
        blank=False,
        related_name='recipes'
    )
    pub_date = models.DateTimeField(
        verbose_name='Дата добавления',
        auto_now_add=True
    )

    class Meta:
        verbose_name = 'рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ['-pub_date']

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
        blank=False,
        null=False,
    )
    ingredient = models.ForeignKey(
        Ingredient,
        verbose_name='Ингредиент',
        on_delete=models.CASCADE,
        blank=False,
        null=False,
    )
    amount = models.IntegerField(
        verbose_name='Количество',
        blank=False,
        null=False,
    )

    class Meta:
        verbose_name = 'ингредиент для рецепта'
        verbose_name_plural = 'Ингредиенты для рецепта'
        constraints = [
            models.UniqueConstraint(
                fields=('recipe', 'ingredient'),
                name='unique_recipe_ingredient'
            )
        ]

    def __str__(self):
        return (f'{self.recipe.name} содержит {self.ingredient.name} '
                f'в количестве {self.amount} {self.ingredient.measurement_unit}')
