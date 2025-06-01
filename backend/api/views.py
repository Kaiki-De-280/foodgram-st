import base64

from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import (viewsets, filters, status)
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import (
    IsAuthenticated,
    AllowAny,
    IsAuthenticatedOrReadOnly,
)
from django.shortcuts import get_object_or_404
from django.http import (HttpResponse, Http404)
from django.db.models import Sum, F
from django.urls import reverse

from djoser.views import UserViewSet as DjoserUserViewSet

from .pagination import UserSubscrRecipePagination
from .permissions import IsAuthorOrReadOnly
from .filters import RecipeFilter
from .serializers import (
    RecipeCreateUpdateSerializer,
    RecipeMinifiedSerializer,
    SubscriptionSerializer,
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
    permission_classes = [AllowAny]
    pagination_class = UserSubscrRecipePagination
    serializer_class = UserSerializer
    lookup_field = 'pk'
    lookup_value_regex = r'\d+'  # id обязательно число

    def get_permissions(self):
        if self.action in ['me', 'set_password', 'avatar', 'subscriptions', 'subscribe']:
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
                return Response(
                    {'detail': 'Нельзя подписаться на себя.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            subscription, created = Subscription.objects.get_or_create(
                user=request.user,
                author=author
            )
            if not created:
                usr = subscription.author.username
                return Response(
                    {'detail': f'Вы уже подписаны на пользователя {usr} с id = {pk}.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            data = SubscriptionSerializer(author,
                                          context={'request': request}).data
            return Response(data, status=status.HTTP_201_CREATED)

        try:
            subscription = get_object_or_404(
                Subscription,
                user=request.user,
                author=author
            )
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Http404:
            usr = User.objects.get(pk=pk)
            return Response(
                {'detail': f'Вы не подписаны на пользователя {usr} с id = {pk}.'},
                status=status.HTTP_400_BAD_REQUEST
            )

    # Список подписок текущего пользователя
    @action(detail=False, methods=['get'], url_path='subscriptions')
    def list_subscriptions(self, request):
        """
        GET /api/users/subscriptions/  => список подписок текущего пользователя
        """
        authors = User.objects.filter(subscribing__user=request.user)
        page = self.paginate_queryset(authors)
        serializer = SubscriptionSerializer(page, many=True,
                                            context={'request': request})
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
        encoded_id = base64.urlsafe_b64encode(str(pk).encode()).decode().rstrip('=')
        short_url = request.build_absolute_uri(
            reverse('short-link-redirect', kwargs={'encoded_id': encoded_id})
        )
        return Response({'short-link': short_url})

    def perform_create(self, serializer):
        recipe = serializer.save(author=self.request.user)
        read = RecipeListSerializer(
            recipe, context={'request': self.request}
        )
        serializer.instance = recipe
        serializer._data = read.data

    def perform_update(self, serializer):
        recipe = serializer.save()
        read = RecipeListSerializer(
            recipe,
            context={'request': self.request}
        )
        serializer.instance = recipe
        serializer._data = read.data

    # Получение рецепта
    def _get_recipe(self):
        recipe_id = self.kwargs.get('pk')
        return get_object_or_404(Recipe, pk=recipe_id)

    # Добавление / Удаление в избранном
    @action(detail=True, methods=['post', 'delete'], url_path='favorite')
    def create_favorite(self, request, pk=None):
        recipe = self._get_recipe()
        user = request.user

        if request.method == 'POST':
            if Favorite.objects.filter(user=user, recipe=recipe).exists():
                return Response(
                    {'detail': 'Рецепт уже находится в избранном.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            Favorite.objects.create(user=user, recipe=recipe)
            serializer = RecipeMinifiedSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        favorite = Favorite.objects.filter(user=user, recipe=recipe).first()
        if not favorite:
            return Response(
                {'detail': "Рецепта нет в избранном."},
                status=status.HTTP_400_BAD_REQUEST
            )
        favorite.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    # Добавление / Удаление в списке покупок
    @action(detail=True, methods=['post', 'delete'], url_path='shopping_cart')
    def shopping_cart(self, request, pk=None):
        recipe = self._get_recipe()
        user = request.user

        if request.method == 'POST':
            if ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
                return Response(
                    {"detail": "Рецепт уже находится в списке покупок."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            ShoppingCart.objects.create(user=user, recipe=recipe)
            serializer = RecipeMinifiedSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        cart_item = ShoppingCart.objects.filter(user=user,
                                                recipe=recipe).first()
        if not cart_item:
            return Response(
                {"detail": "Рецепт не находится в списке покупок."},
                status=status.HTTP_400_BAD_REQUEST
            )
        cart_item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    # Скачивание списка покупок
    @action(detail=False, methods=['get'], url_path='download_shopping_cart')
    def download_shopping_cart(self, request):
        user = request.user
        qs = RecipeIngredient.objects.filter(recipe__in_shoppingcarts__user=user)
        aggregated = (
            qs.values(
                name=F('ingredient__name'),
                unit=F('ingredient__measurement_unit')
            )
            .annotate(total_amount=Sum('amount'))
            .order_by('name')
        )
        lines = [
            f"{item['name']} ({item['unit']}) — {item['total_amount']}"
            for item in aggregated
        ]
        body = "\n".join(lines)
        response = HttpResponse(body, content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename="shopping_list.txt"'
        return response
