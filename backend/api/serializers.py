from rest_framework import serializers

from djoser.serializers import (
    UserSerializer as DjoserUserSerializer,)
from django.contrib.auth.validators import UnicodeUsernameValidator

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
    username = serializers.CharField(required=True,
                                     validators=[UnicodeUsernameValidator()],)

    class Meta(DjoserUserSerializer.Meta):
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'password',
            'is_subscribed',
            'avatar',
        )
        extra_kwargs = {
            'first_name': {'required': True, 'max_length': 150},
            'last_name': {'required': True, 'max_length': 150},
            'password': {'write_only': True},
            'id': {'read_only': True},
        }

    def get_is_subscribed(self, usr):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return User.objects.filter(
            subscriptions__user=request.user,
            subscribing__author=usr
        ).exists()

    def validate_username(self, value):
        if len(value) > 150 or len(value) < 0:
            raise serializers.ValidationError('Значение юзернейма должно быть от 1 до 150 символов.')
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError('Пользователь с таким юзернеймом уже существует.')
        return value

    def validate_first_name(self, value):
        if len(value) > 150 or len(value) < 0:
            raise serializers.ValidationError('Значение имени должно быть от 1 до 150 символов.')
        return value

    def validate_last_name(self, value):
        if len(value) > 150 or len(value) < 0:
            raise serializers.ValidationError('Значение фамилии должно быть от 1 до 150 символов.')
        return value


class AvatarSerializer(serializers.ModelSerializer):
    """
    Установка и удаление аватара пользователя.
    """
    avatar = Base64ImageField(required=True)

    class Meta:
        model = User
        fields = ('avatar',)


class SubscriptionSerializer(UserSerializer):
    """
    Просмотр подписок пользователя.
    """
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(source='user_recipes.count')

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

    # Ограничение количества рецептов
    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.query_params.get('recipes_limit')
        _qs = obj.user_recipes.all()
        if limit and limit.isdigit():
            _qs = _qs[:int(limit)]
        return RecipeMinifiedSerializer(_qs,
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
        source='products',
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
            and recipe.in_favorites.filter(user=user).exists()
        )

    def get_is_in_shopping_cart(self, recipe):
        user = self.context['request'].user
        return (
            user.is_authenticated
            and recipe.in_shoppingcarts.filter(user=user).exists()
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
        extra_kwargs = {
            'ingredients': {'required': True},
        }

    def _save_ingredients(self, recipe, ingredients_data):
        recipe.products.all().delete()
        RecipeIngredient.objects.bulk_create([
            RecipeIngredient(
                recipe=recipe,
                ingredient=item['ingredient'],
                amount=item['amount']
            )
            for item in ingredients_data
        ])

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        recipe = super().create(validated_data)
        self._save_ingredients(recipe, ingredients_data)
        return Recipe.objects.get(pk=recipe.pk)

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('ingredients', None)

        # Ингредиенты должны быть обязательны, проверки на наличие
        # в родительском update-е нет
        if ingredients_data is None:
            raise serializers.ValidationError(
                {'ingredients': ['Это поле обязательно при обновлении.']}
            )
        # Сначала выполним это, т.к в противном случае, если родительский метод
        # ляжет, ингредиенты уже будут сохранены т.е будет нарушена целостность
        instance = super().update(instance, validated_data)

        if ingredients_data is not None:
            self._save_ingredients(instance, ingredients_data)
        # Ну и вернём instance
        return instance

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
