from rest_framework import mixins, viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from .serializers import SetPasswordSerializer
from .serializers import (
    UserSerializer,
    CreateUserSerializer,
    AvatarSerializer,
    SubscriptionSerializer
)

from .models import Subscription
from .pagination import BasePagination

from django.contrib.auth import get_user_model
User = get_user_model()


class UserViewSet(mixins.ListModelMixin,
                  mixins.RetrieveModelMixin,
                  mixins.CreateModelMixin,
                  viewsets.GenericViewSet):
    """
    Просмотр и создание пользователей:
    POST    /api/users/    => регистрация нового пользователя
    GET    /api/users/    => список пользователей
    GET    /api/users/{id}/    => детали пользователя
    """
    lookup_value_regex = r'\d+'  # id обязательно число
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    pagination_class = BasePagination

    def get_serializer_class(self):
        if self.action == 'create':
            return CreateUserSerializer
        return UserSerializer


class ProfileAvatarViewSet(viewsets.GenericViewSet):
    """
    Работа с профилем пользователя
    GET       /api/users/me/             => профиль текущего пользователя
    POST      /api/users/set_password/   => смена пароля
    PUT       /api/users/me/avatar/      => загрузить / заменить аватар
    PATCH     /api/users/me/avatar/      => частичное обновление аватара
    DELETE    /api/users/me/avatar/      => удалить аватар
    """
    permission_classes = [IsAuthenticated]

    # Профиль
    @action(detail=False, methods=['get'], url_path='me')
    def me(self, request):
        serializer = UserSerializer(request.user,
                                    context={'request': request})
        return Response(serializer.data)

    # Смена пароля
    @action(detail=False, methods=['post'], url_path='set_password')
    def set_password(self, request):
        serializer = SetPasswordSerializer(data=request.data,
                                           context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    # Смена аватара
    @action(detail=False, methods=['put'], url_path='me/avatar')
    def set_avatar(self, request):
        serializer = AvatarSerializer(
            request.user,
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'avatar': serializer.data['avatar']})

    # Удаление аватара
    @action(detail=False, methods=['delete'], url_path='me/avatar')
    def delete_avatar(self, request):
        request.user.avatar.delete(save=True)
        return Response(status=status.HTTP_204_NO_CONTENT)


class SubscriptionViewSet(viewsets.GenericViewSet):
    """
    Управление подписками:
    POST    /api/users/{id}/subscribe/    => подписаться на автора
    DELETE  /api/users/{id}/subscribe/    => отписаться
    GET    /api/users/subscriptions/   => список подписок текущего пользователя
    """
    queryset = User.objects.all()
    permission_classes = [IsAuthenticated]
    pagination_class = BasePagination

    # Подписаться и отписаться
    @action(detail=True, methods=['post', 'delete'], url_path='subscribe')
    def subscribe(self, request, pk=None):
        """
        POST    /api/users/{pk}/subscribe/    => подписаться
        DELETE  /api/users/{pk}/subscribe/    => отписаться
        """
        author = self.get_object()

        if request.user == author:
            return Response(
                {'detail': 'Нельзя подписаться на себя.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if request.method == 'POST':
            subscription, created = Subscription.objects.get_or_create(
                user=request.user,
                author=author
            )
            if not created:
                return Response(
                    {'detail': 'Вы уже подписаны на этого пользователя.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            data = SubscriptionSerializer(author,
                                          context={'request': request}).data
            return Response(data, status=status.HTTP_201_CREATED)

        deleted, _ = Subscription.objects.filter(
            user=request.user,
            author=author
        ).delete()
        if deleted == 0:
            return Response(
                {'detail': 'Вы не подписаны на этого пользователя.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    # Список подписок текущего пользователя
    @action(detail=False, methods=['get'], url_path='subscriptions')
    def list_subscriptions(self, request):
        authors = User.objects.filter(subscribers__user=request.user)
        page = self.paginate_queryset(authors)
        serializer = SubscriptionSerializer(page, many=True,
                                            context={'request': request})
        return self.get_paginated_response(serializer.data)
