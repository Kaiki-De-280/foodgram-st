from django.contrib import admin
from .models import Recipe, RecipeIngredient


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 0
    verbose_name = 'Ингредиент для рецепта'
    verbose_name_plural = 'Ингредиенты для рецепта'
    readonly_fields = ()


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display_links = ('name',)
    list_display = (
        'id',
        'name',
        'author',
        'cooking_time',
        'pub_date',
        'favorites_count',
    )
    readonly_fields = ('favorites_count',)
    fieldsets = (
        (None, {
            'fields': ('name','author','cooking_time','image','text')
        }),
        ('Статистика', {
            'fields': ('favorites_count',),
            'description': 'Сколько раз рецепт добавлен в избранное'
        }),
    )
    list_filter = (
        'author',
        'pub_date',
    )
    search_fields = (
        'name',
        'author__username',
        'author__email',
    )
    ordering = ('-pub_date',)
    inlines = [RecipeIngredientInline]

    @admin.display(description='В избранном у ')
    def favorites_count(self, obj):
        return obj.favorited_by.count()


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = (
        'recipe',
        'ingredient',
        'amount',
    )
    list_filter = (
        'ingredient',
        'recipe',
    )
    search_fields = (
        'recipe__name',
        'ingredient__name',
    )
