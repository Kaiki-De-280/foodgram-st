from django_filters import rest_framework as filters

from recipes.models import Recipe


class RecipeFilter(filters.FilterSet):
    """
    Фильтрация рецептов по:
    - Id автора
    - Наличию в избранном
    - Наличию в корзине
    """
    author = filters.NumberFilter(field_name='author__id')
    is_favorited = filters.NumberFilter(method='filter_is_favorited')
    is_in_shopping_cart = filters.NumberFilter(method='filter_in_shopping_cart')

    class Meta:
        model = Recipe
        fields = ['author', 'is_favorited', 'is_in_shopping_cart']

    def filter_is_favorited(self, recipes, name, value):
        user = self.request.user

        if not user.is_authenticated:
            return recipes.none() if value == 1 else recipes

        if value == 1:
            return recipes.filter(in_favorites__user=user)
        if value == 0:
            return recipes.exclude(in_favorites__user=user)
        return recipes

    def filter_in_shopping_cart(self, recipes, name, value):
        user = self.request.user

        if not user.is_authenticated:
            return recipes.none() if value == 1 else recipes

        if value == 1:
            return recipes.filter(in_shoppingcarts__user=user)
        if value == 0:
            return recipes.exclude(in_shoppingcarts__user=user)
        return recipes
