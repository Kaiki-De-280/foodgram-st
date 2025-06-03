from django_filters.rest_framework import DjangoFilterBackend
from datetime import datetime as dt
import io

from rest_framework import (viewsets, filters, status, serializers,)
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import (
    IsAuthenticatedOrReadOnly,
    IsAuthenticated,
    AllowAny,
)
from django.shortcuts import get_object_or_404
from django.http import FileResponse
from django.db.models import Sum, F
from django.urls import reverse

from djoser.views import UserViewSet as DjoserUserViewSet

from .pagination import UserSubscrRecipePagination
from .permissions import IsAuthorOrReadOnly
from .filters import RecipeFilter
from .serializers import (
    UserSubscriptionsListSerializer,
    RecipeCreateUpdateSerializer,
    RecipeMinifiedSerializer,
    RecipeListSerializer,
    IngredientSerializer,
    AvatarSerializer,
    UserSerializer,
)
from recipes.models import (
    RecipeIngredient,
    ShoppingCart,
    Subscription,
    Ingredient,
    Favorite,
    Recipe,
)

from django.contrib.auth import get_user_model
User = get_user_model()


# Ингредиент
class IngredientSearchFilter(filters.SearchFilter):
    search_param = 'name'


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Получение списка и единичного ингредиента.
    GET    /api/ingredients/    => получить список всех ингредиентов
    GET    /api/ingredients/{id}/    => получить ингредиент по id
    """
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [AllowAny]
    filter_backends = [IngredientSearchFilter]
    search_fields = ['^name',]
    pagination_class = None


# Пользователи и подписки
class UserViewSet(DjoserUserViewSet):
    """
    Единый вьюсет для работы с пользователями:
    - Регистрация нового пользователя
    - Просмотр пользователей
    - Просмотр профиля
    - Управление аватаром
    - Управление подписками
    """
    queryset = User.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = UserSubscrRecipePagination
    serializer_class = UserSerializer
    lookup_field = 'pk'
    lookup_value_regex = r'\d+'  # id обязательно число

    def get_permissions(self):
        if self.action in ('me',):
            return [IsAuthenticated()]
        return super().get_permissions()

    # Смена / Удаление аватара
    @action(detail=False, methods=['put', 'delete'], url_path='me/avatar')
    def avatar(self, request):
        if request.method == 'PUT':
            serializer = AvatarSerializer(
                request.user,
                data=request.data,
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({'avatar': serializer.data['avatar']})

        request.user.avatar.delete(save=True)
        return Response(status=status.HTTP_204_NO_CONTENT)

    # Подписаться и отписаться
    @action(detail=True, methods=['post', 'delete'], url_path='subscribe')
    def subscribe(self, request, pk=None):
        """
        POST    /api/users/{pk}/subscribe/    => подписаться
        DELETE  /api/users/{pk}/subscribe/    => отписаться
        """
        author = self.get_object()

        if request.method == 'POST':
            if request.user == author:
                raise serializers.ValidationError('Нельзя подписаться на себя.')
            subscription, created = Subscription.objects.get_or_create(
                user=request.user,
                author=author
            )
            if not created:
                usr = subscription.author.username
                raise serializers.ValidationError(
                    f'Вы уже подписаны на пользователя {usr} с id = {pk}.'
                )
            data = UserSubscriptionsListSerializer(
                author,
                context={'request': request},
            ).data
            return Response(data, status=status.HTTP_201_CREATED)

        # If request.method == 'DELETE'
        subscription = get_object_or_404(
            Subscription,
            user=request.user,
            author=author
        )
        subscription.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    # Список подписок текущего пользователя
    @action(detail=False, methods=['get'], url_path='subscriptions')
    def list_subscriptions(self, request):
        """
        GET /api/users/subscriptions/  => список подписок текущего пользователя
        """
        authors = User.objects.filter(authors__user=request.user)
        page = self.paginate_queryset(authors)
        serializer = UserSubscriptionsListSerializer(
            page, many=True,
            context={'request': request}
        )
        return self.get_paginated_response(serializer.data)


# Рецепты
class RecipeViewSet(viewsets.ModelViewSet):
    """
    Единый вьюсет для работы с:
    - Рецептами
    - Списками избранного и покупок
    - Получение короткой ссылки на рецепт
    """
    queryset = Recipe.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly,
                          IsAuthorOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter
    pagination_class = UserSubscrRecipePagination

    def get_permissions(self):
        if self.action in ('favorite',
                           'shopping_cart',
                           'download_shopping_cart',):
            return [IsAuthenticated()]
        return super().get_permissions()

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve', 'get_link'):
            return RecipeListSerializer
        return RecipeCreateUpdateSerializer

    @action(detail=True, methods=['get'], url_path='get-link')
    def get_link(self, request, pk=None):
        """
        Получение ссылки на рецепт.
        """
        short_url = request.build_absolute_uri(
            reverse('short-link-redirect', kwargs={'recipe_id': pk})
        )
        return Response({'short-link': short_url})

    def perform_create(self, serializer):
        # Нет это не лишние строки, т.к. именно они отвечают
        # за то, что Response samples будет как в документации.
        # Я не знаю как это реализовать без подмены
        # сериализатора при возвращении ответа.
        # Если такая возможность есть, то подскажите.
        # От метода create вы написали избавиться и заменить его на
        # perform* версию.
        recipe = serializer.save(author=self.request.user)
        read = RecipeListSerializer(
            recipe, context={'request': self.request}
        )
        serializer._data = read.data

    def perform_update(self, serializer):
        # Аналогично предыдущему.
        recipe = serializer.save()
        read = RecipeListSerializer(
            recipe,
            context={'request': self.request}
        )
        serializer.instance = recipe
        serializer._data = read.data

    def _create_delete_favorite_shoppingcart(
        self,
        request,
        model
    ):
        """
        Общий алгоритм поведения при добавлении или удалении из избранного и списка покупок.
        model  — модель: Favorite или ShoppingCart.
        """
        recipe = self.get_object()
        user = request.user

        if request.method == 'POST':
            obj, created = model.objects.get_or_create(
                user=user,
                recipe=recipe
            )
            if not created:
                raise serializers.ValidationError(
                    f'Рецепт {recipe.name} уже находится в {model._meta.verbose_name}.'
                )
            serializer = RecipeMinifiedSerializer(
                recipe,
                context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        # request.method == 'DELETE'
        get_object_or_404(model, user=user, recipe=recipe).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    # Добавление / Удаление в избранном
    @action(detail=True, methods=['post', 'delete'], url_path='favorite')
    def favorite(self, request, pk=None):
        return self._create_delete_favorite_shoppingcart(
            request=request,
            model=Favorite
        )

    # Добавление / Удаление в списке покупок
    @action(detail=True, methods=['post', 'delete'], url_path='shopping_cart')
    def shopping_cart(self, request, pk=None):
        return self._create_delete_favorite_shoppingcart(
            request=request,
            model=ShoppingCart
        )

    # Скачивание списка покупок
    @action(detail=False, methods=['get'], url_path='download_shopping_cart')
    def download_shopping_cart(self, request):
        user = request.user

        # Собираем продукты
        products = RecipeIngredient.objects.filter(
            recipe__shoppingcarts__user=user
        ).values(
            name=F('ingredient__name'),
            unit=F('ingredient__measurement_unit')
        ).annotate(
            total_amount=Sum('amount')
        ).order_by('name')

        # Собираем рецепты
        recipes_qs = Recipe.objects.filter(
            shoppingcarts__user=user
        ).distinct().select_related('author')

        # Дата составления списка
        today = dt.now().strftime('%d.%m.%Y')

        # Формируем ответ
        body_text = '\n'.join([
            f'Список покупок от {today}',
            'Нужные продукты:',
            *[
                f'{num}. {item["name"].capitalize()} ({item["unit"]}) — {item["total_amount"]}'
                for num, item in enumerate(products, start=1)
            ],
            '',
            'Для рецептов:',
            *[
                f'- {recipe.name} (автор: {recipe.author.username})'
                for recipe in recipes_qs
            ],
        ])

        buffer = io.BytesIO()
        buffer.write(body_text.encode('utf-8'))
        buffer.seek(0)

        return FileResponse(
            buffer,
            as_attachment=True,
            filename='shopping_list.txt',
            content_type='text/plain'
        )
