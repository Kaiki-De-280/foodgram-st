from rest_framework import serializers

from djoser.serializers import (
    UserSerializer as DjoserUserSerializer,)

from .utils import Base64ImageField
from recipes.models import (
    RecipeIngredient,
    Ingredient,
    Recipe,
)

from django.contrib.auth import get_user_model
User = get_user_model()


# Просто в просмотре ингредиента
class IngredientSerializer(serializers.ModelSerializer):
    """
    Получение списка и единичного ингредиента.
    """
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


# В просмотре рецепта
class IngredientInRecipeSerializer(serializers.ModelSerializer):
    """
    Просмотр ингредиентов внутри рецепта.
    """
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(source='ingredient.measurement_unit')

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')
        read_only_fields = fields


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


# Пользователь
class UserSerializer(DjoserUserSerializer):
    """
    Сериализатор для пользователя.
    """
    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.ImageField(use_url=True, required=False)

    class Meta(DjoserUserSerializer.Meta):
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar',
        )
        read_only_fields = fields

    def get_is_subscribed(self, usr):
        request = self.context.get('request')
        return (
            request
            and request.user.is_authenticated
            and User.objects.filter(
                subscriptions__user=request.user,
                subscriptions__author=usr
            ).exists()
        )


# В добавлении аватара
class AvatarSerializer(serializers.ModelSerializer):
    """
    Установка аватара пользователя.
    """
    avatar = Base64ImageField(required=True)

    class Meta:
        model = User
        fields = ('avatar',)


class UserSubscriptionsListSerializer(UserSerializer):
    """
    Просмотр подписок пользователя.
    """
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(source='recipes.count')

    class Meta():
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
            'avatar',
        )
        read_only_fields = fields

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.query_params.get('recipes_limit')
        _qs = obj.recipes.all()
        if limit and limit.isdigit():
            _qs = _qs[:int(limit)]
        return RecipeMinifiedSerializer(
            _qs,
            many=True,
            context={'request': request}
        ).data


class RecipeListSerializer(serializers.ModelSerializer):
    """
    Просмотр рецепта или списка рецептов.
    GET      /api/recipes/
    GET      /api/recipes/{id}/
    POST     /api/recipes/        (response)
    PATCH    /api/recipes/{id}/  (response)
    """
    author = UserSerializer()
    ingredients = IngredientInRecipeSerializer(
        many=True,
        source='recipeingredients',
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

    def get_is_favorited(self, recipe):
        user = self.context['request'].user
        return (
            user.is_authenticated
            and recipe.favorites.filter(user=user).exists()
        )

    def get_is_in_shopping_cart(self, recipe):
        user = self.context['request'].user
        return (
            user.is_authenticated
            and recipe.shoppingcarts.filter(user=user).exists()
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
        read_only_fields = fields


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Создание / обновление рецепта.
    """
    image = Base64ImageField()
    ingredients = IngredientAmountSerializer(many=True)
    cooking_time = serializers.IntegerField(min_value=1)

    class Meta:
        model = Recipe
        fields = (
            'ingredients', 'image',
            'name', 'text', 'cooking_time',
        )

    def _save_ingredients(self, recipe, ingredients_data):
        recipe.recipeingredients.all().delete()
        RecipeIngredient.objects.bulk_create(
            RecipeIngredient(
                recipe=recipe,
                ingredient=item['ingredient'],
                amount=item['amount']
            )
            for item in ingredients_data
        )

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        recipe = super().create(validated_data)
        self._save_ingredients(recipe, ingredients_data)
        return Recipe.objects.get(pk=recipe.pk)

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('ingredients', None)
        self._save_ingredients(instance, ingredients_data)
        return super().update(instance, validated_data)

    def validate_ingredients(self, product):
        if not product:
            raise serializers.ValidationError(
                'Нужно указать хотя бы один продукт.'
            )
        ids = [item['ingredient'].id for item in product]
        if len(ids) != len(set(ids)):
            raise serializers.ValidationError(
                'Продукты в рецепте должны быть уникальны.'
            )
        return product

    def validate(self, attrs):
        if self.instance and 'ingredients' not in attrs:
            raise serializers.ValidationError({
                'ingredients': 'Это поле обязательно при обновлении.'
            })
        return attrs
