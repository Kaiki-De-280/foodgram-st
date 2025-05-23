from rest_framework import mixins, status
from rest_framework.viewsets import GenericViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.db.models import Sum, F

from recipes.models import Recipe, RecipeIngredient
from recipes.serializers import RecipeMinifiedSerializer
from .models import Favorite, ShoppingCart


class FavoriteViewSet(mixins.CreateModelMixin,
                      mixins.DestroyModelMixin,
                      GenericViewSet):
    """
    Избранное: добавление / удаление.
    POST    /api/recipes/{id}/favorite/    => добавить в избранное
    DELETE    /api/recipes/{id}/favorite/    => удалить из избранного
    """
    permission_classes = [IsAuthenticated]
    serializer_class = RecipeMinifiedSerializer
    lookup_url_kwarg = 'recipe_id'

    # Получение рецепта
    def get_recipe(self):
        recipe_id = self.kwargs.get(self.lookup_url_kwarg)
        return get_object_or_404(Recipe, pk=recipe_id)

    # Добавление в избранное
    def create(self, request, *args, **kwargs):
        recipe = self.get_recipe()
        user = request.user
        if Favorite.objects.filter(user=user, recipe=recipe).exists():
            return Response(
                {'detail': 'Рецепт уже находится в избранном.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        Favorite.objects.create(user=user, recipe=recipe)
        serializer = self.get_serializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    # Удаление из избранного
    def destroy(self, request, *args, **kwargs):
        recipe = self.get_recipe()
        user = request.user
        favorite = Favorite.objects.filter(user=user, recipe=recipe).first()
        if not favorite:
            return Response(
                {'detail': "Рецепта нет в избранном."},
                status=status.HTTP_400_BAD_REQUEST
            )
        favorite.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ShoppingCartViewSet(mixins.CreateModelMixin,
                          mixins.DestroyModelMixin,
                          GenericViewSet):
    """
    Список покупок: добавление / удаление.
    POST    /api/recipes/{id}/shopping_cart/    => добавить в список покупок
    DELETE    /api/recipes/{id}/shopping_cart/    => удалить из списка покупок
    """
    permission_classes = [IsAuthenticated]
    serializer_class = RecipeMinifiedSerializer
    lookup_url_kwarg = 'recipe_id'

    # Получение рецепта
    def get_recipe(self):
        recipe_id = self.kwargs.get(self.lookup_url_kwarg)
        return get_object_or_404(Recipe, pk=recipe_id)

    # Добавление в список покупок
    def create(self, request, *args, **kwargs):
        recipe = self.get_recipe()
        user = request.user
        if ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
            return Response(
                {"detail": "Рецепт уже находится в списке покупок."},
                status=status.HTTP_400_BAD_REQUEST
            )
        ShoppingCart.objects.create(user=user, recipe=recipe)
        serializer = self.get_serializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    # Удаление из списка покупок
    def destroy(self, request, *args, **kwargs):
        recipe = self.get_recipe()
        user = request.user
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
        qs = RecipeIngredient.objects.filter(recipe__in_carts__user=user)
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
