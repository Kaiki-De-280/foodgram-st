from rest_framework import serializers
from djoser.serializers import (
    UserCreateSerializer as DjoserUserCreateSerializer,
    SetPasswordSerializer as DjoserSetPasswordSerializer)
from django.contrib.auth.validators import UnicodeUsernameValidator

from .models import Subscription
from recipes.serializers import RecipeMinifiedSerializer
from .utils import Base64ImageField


from django.contrib.auth import get_user_model
User = get_user_model()


class CreateUserSerializer(DjoserUserCreateSerializer):
    """
    Регистрация нового пользователя.
    """
    username = serializers.CharField(required=True,
                                     validators=[UnicodeUsernameValidator()],)
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)

    class Meta(DjoserUserCreateSerializer.Meta):
        model = User
        fields = ('id', 'email', 'username', 'first_name', 'last_name', 'password')
        read_only_fields = ('id',)

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


class SetPasswordSerializer(DjoserSetPasswordSerializer):
    """
    Смена пароля.
    """
    def save(self, **kwargs):
        user = self.context['request'].user
        new_password = self.validated_data['new_password']
        user.set_password(new_password)
        user.save()
        return user


class UserSerializer(serializers.ModelSerializer):
    """
    Просмотр профиля пользователя.
    """
    avatar = serializers.ImageField(use_url=True)
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
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

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return Subscription.is_subscribed(request.user, obj)


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

    # Ограничение количества рецептов
    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.query_params.get('recipes_limit')
        _qs = obj.recipes.all()
        if limit and limit.isdigit():
            _qs = _qs[:int(limit)]
        return RecipeMinifiedSerializer(_qs,
                                        many=True,
                                        context={'request': request}
                                        ).data
