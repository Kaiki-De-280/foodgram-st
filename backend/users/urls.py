from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import UserViewSet, ProfileAvatarViewSet, SubscriptionViewSet

router = DefaultRouter()

router.register(r'users', UserViewSet, basename='user')


urlpatterns = [

    # Аунтефикация
    path('auth/', include('djoser.urls.authtoken')),

    #  Профиль
    path(
        'users/me/',
        ProfileAvatarViewSet.as_view({'get': 'me'}),
        name='user-me'
    ),

    # Смена пароля
    path(
        'users/set_password/',
        ProfileAvatarViewSet.as_view({'post': 'set_password'}),
        name='user-set-password'
    ),

    # Смена и удаление аватара
    path(
        'users/me/avatar/',
        ProfileAvatarViewSet.as_view({
            'put': 'set_avatar',
            'delete': 'delete_avatar'
        }),
        name='user-avatar'
    ),

    # Подписаться и отписаться
    path(
        'users/<int:pk>/subscribe/',
        SubscriptionViewSet.as_view({
            'post': 'subscribe',
            'delete': 'subscribe'
        }),
        name='user-subscribe'
    ),

    # Список подписок
    path(
        'users/subscriptions/',
        SubscriptionViewSet.as_view({'get': 'list_subscriptions'}),
        name='user-subscriptions'
    ),

    path('', include(router.urls)),
]
