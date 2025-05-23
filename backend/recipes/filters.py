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

    def filter_is_favorited(self, queryset, name, value):
        user = self.request.user

        if not user.is_authenticated:
            return queryset.none() if value == 1 else queryset

        if value == 1:
            return queryset.filter(favorited_by__user=user)
        if value == 0:
            return queryset.exclude(favorited_by__user=user)
        return queryset

    def filter_in_shopping_cart(self, queryset, name, value):
        user = self.request.user

        if not user.is_authenticated:
            return queryset.none() if value == 1 else queryset

        if value == 1:
            return queryset.filter(in_carts__user=user)
        if value == 0:
            return queryset.exclude(in_carts__user=user)
        return queryset
