from django.contrib import admin

from favorites_cart.models import Favorite, ShoppingCart


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'recipe',
    )
    search_fields = (
        'user__username',
        'user__email',
        'recipe__name',
    )
    list_filter = (
        'user',
    )


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'recipe',
    )
    search_fields = (
        'user__username',
        'user__email',
        'recipe__name',
    )
    list_filter = (
        'user',
    )
