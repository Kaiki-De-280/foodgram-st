from django.db import models

from users.models import CustomUser
from recipes.models import Recipe


class Favorite(models.Model):
    """
    Модель списка избранного.
    """
    user = models.ForeignKey(
        CustomUser,
        verbose_name='Пользователь',
        on_delete=models.CASCADE,
        blank=False,
        null=False,
    )
    recipe = models.ForeignKey(
        Recipe,
        verbose_name='Рецепт',
        on_delete=models.CASCADE,
        blank=False,
        null=False,
        related_name='favorited_by',
    )

    class Meta:
        verbose_name = 'избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_favorite'
            )
        ]

    def __str__(self):
        return f'Рецепт {self.recipe.name} в избранном у {self.user.username}'


class ShoppingCart(models.Model):
    """
    Модель списка покупок.
    """
    user = models.ForeignKey(
        CustomUser,
        verbose_name='Пользователь',
        on_delete=models.CASCADE,
        blank=False,
        null=False,
    )
    recipe = models.ForeignKey(
        Recipe,
        verbose_name='Рецепт',
        on_delete=models.CASCADE,
        blank=False,
        null=False,
        related_name='in_carts',
    )

    class Meta:
        verbose_name = 'список покупок'
        verbose_name_plural = 'Список покупок'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_cart_item'
            )
        ]

    def __str__(self):
        return f'Рецепт {self.recipe.name} в корзине у {self.user.username}'
