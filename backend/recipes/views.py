from django_filters.rest_framework import DjangoFilterBackend
from recipes.filters import RecipeFilter

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.reverse import reverse

from .models import Recipe
from users.pagination import BasePagination
from .serializers import (
    RecipeListSerializer,
    RecipeCreateUpdateSerializer,
)
from .permissions import IsAuthorOrReadOnly


class RecipeViewSet(viewsets.ModelViewSet):
    """
    Работа с рецептами:
    GET      /api/recipes/           => список рецептов
    POST     /api/recipes/           => создать рецепт
    GET      /api/recipes/{id}/      => получить детали рецепта
    PATCH    /api/recipes/{id}/      => частично обновить
    DELETE   /api/recipes/{id}/      => удалить рецепт

    GET      /api/recipes/{id}/get-link/ => получить короткую ссылку на рецепт
    """
    queryset = Recipe.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter
    pagination_class = BasePagination

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve', 'get_link'):
            return RecipeListSerializer
        return RecipeCreateUpdateSerializer

    @action(detail=True, methods=['get'], url_path='get-link')
    def get_link(self, request, pk=None):
        """
        Получение ссылки на рецепт.
        """
        recipe = self.get_object()
        return Response(
            {'short-link': request.build_absolute_uri(f'/recipes/{recipe.pk}')},
            status=status.HTTP_200_OK
        )

    def create(self, request, *args, **kwargs):
        create_serializer = self.get_serializer(data=request.data)
        create_serializer.is_valid(raise_exception=True)
        recipe = create_serializer.save()
        read = RecipeListSerializer(
            recipe, context={'request': request}
        )
        return Response(read.data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = RecipeCreateUpdateSerializer(
            instance,
            data=request.data,
            partial=False,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        recipe = serializer.save()
        read = RecipeListSerializer(
            recipe,
            context={'request': request}
        )
        return Response(read.data, status=status.HTTP_200_OK)
