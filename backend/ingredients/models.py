from django.db import models


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
