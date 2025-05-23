from django.urls import path
from .views import FavoriteViewSet, ShoppingCartViewSet


urlpatterns = [

    # Избранное: добавление / удаление
    path(
        'recipes/<int:recipe_id>/favorite/',
        FavoriteViewSet.as_view({
            'post': 'create',
            'delete': 'destroy',
        }),
        name='recipe-favorite'
    ),

    # Список покупок: добавление / удаление
    path(
        'recipes/<int:recipe_id>/shopping_cart/',
        ShoppingCartViewSet.as_view({
            'post': 'create',
            'delete': 'destroy',
        }),
        name='recipe-shopping-cart'
    ),

    # Загрузка списка покупок
    path(
        'recipes/download_shopping_cart/',
        ShoppingCartViewSet.as_view({'get': 'download_shopping_cart'}),
        name='download-shopping-cart'
    ),

]
