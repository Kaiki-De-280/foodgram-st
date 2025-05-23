from rest_framework import serializers
from .models import Ingredient
from recipes.models import RecipeIngredient


class IngredientSerializer(serializers.ModelSerializer):
    """
    Получение списка и единичного ингредиента.
    """
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')
        read_only_fields = fields


# В просмотре рецепта
class IngredientInRecipeSerializer(serializers.ModelSerializer):
    """
    Просмотр ингредиентов внутри рецепта.
    """
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(source='ingredient.measurement_unit')
    amount = serializers.IntegerField(read_only=True)

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


# В создании / обновлении рецепта
class IngredientAmountSerializer(serializers.Serializer):
    """
    Запись ингредиентов при создании / обновлении рецепта.
    """
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source='ingredient',
    )
    amount = serializers.IntegerField(min_value=1)

    def validate_amount(self, value):
        if value < 1:
            raise serializers.ValidationError('Количество ингредиента должно быть не менее 1.')
        return value
