from rest_framework import serializers
from ingredients.serializers import (IngredientInRecipeSerializer,
                                     IngredientAmountSerializer)

from .models import Recipe, RecipeIngredient
from users.utils import Base64ImageField


class RecipeListSerializer(serializers.ModelSerializer):
    """
    Просмотр рецепта или списка рецептов.
    GET      /api/recipes/
    GET      /api/recipes/{id}/
    POST     /api/recipes/        (response)
    PATCH    /api/recipes/{id}/  (response)
    """
    author = serializers.SerializerMethodField()
    ingredients = IngredientInRecipeSerializer(
        many=True,
        source='recipeingredient_set',
        read_only=True
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'author', 'ingredients',
            'is_favorited', 'is_in_shopping_cart',
            'name', 'image', 'text', 'cooking_time',
        )
        read_only_fields = fields

    def get_author(self, obj):
        from users.serializers import UserSerializer
        return UserSerializer(obj.author, context=self.context).data

    def get_is_favorited(self, obj):
        user = self.context['request'].user
        return (
            user.is_authenticated
            and obj.favorited_by.filter(user=user).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        user = self.context['request'].user
        return (
            user.is_authenticated
            and obj.in_carts.filter(user=user).exists()
        )


class RecipeMinifiedSerializer(serializers.ModelSerializer):
    """
    Сериализатор, возвращающий рецепт при добавлении / удалении
    в избранном и списке покупок.
    POST /api/recipes/{id}/shopping_cart/
    POST /api/recipes/{id}/favorite/
    """
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Создание / обновление рецепта.
    """
    image = Base64ImageField()
    ingredients = IngredientAmountSerializer(many=True)

    class Meta:
        model = Recipe
        fields = (
            'ingredients', 'image',
            'name', 'text', 'cooking_time',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        if request and request.method == 'PATCH':
            self.fields['image'].required = False

    def _save_ingredients(self, recipe, ingredients_data):
        RecipeIngredient.objects.filter(recipe=recipe).delete()
        objs = [
            RecipeIngredient(
                recipe=recipe,
                ingredient=item['ingredient'],
                amount=item['amount']
            )
            for item in ingredients_data
        ]
        RecipeIngredient.objects.bulk_create(objs)

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data, author=self.context['request'].user)
        self._save_ingredients(recipe, ingredients_data)
        return recipe

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('ingredients', None)
        for attr, val in validated_data.items():
            setattr(instance, attr, val)
        instance.save()
        if ingredients_data is not None:
            self._save_ingredients(instance, ingredients_data)
        return instance

    def validate_cooking_time(self, value):
        if value < 1:
            raise serializers.ValidationError(
                'Время приготовления должно быть положительным числом.'
            )
        return value

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError(
                'Нужно указать хотя бы один ингредиент.'
            )
        ids = [item['ingredient'].id for item in value]
        if len(ids) != len(set(ids)):
            raise serializers.ValidationError(
                'Ингредиенты в рецепте должны быть уникальны.'
            )
        for item in value:
            amount = item.get('amount')
            if amount is None or amount <= 0:
                raise serializers.ValidationError(
                    f'Количество "{item["ingredient"].name}" должно быть больше нуля.'
                )
        return value
