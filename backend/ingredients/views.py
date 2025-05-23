from rest_framework import viewsets, filters
from rest_framework.permissions import AllowAny

from .models import Ingredient
from .serializers import IngredientSerializer


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
