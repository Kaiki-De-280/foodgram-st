from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from django.utils.safestring import mark_safe
from django.db.models import Count

from .models import (
    RecipeIngredient,
    Subscription,
    ShoppingCart,
    Ingredient,
    Favorite,
    Recipe,
)

from django.contrib.auth import get_user_model
User = get_user_model()


# Список избранного и покупок
@admin.register(Favorite, ShoppingCart)
class FavoriteShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe',)
    search_fields = (
        'user__username',
        'user__email',
        'recipe__name',
    )
    list_filter = ('user',)


# Ингредиенты
class HasRecipesFilter(admin.SimpleListFilter):
    title = ('Есть в рецептах')
    parameter_name = 'has_recipes'

    def lookups(self, request, model_admin):
        return (
            ('yes', ('Используется в рецептах')),
            ('no', ('Не используется в рецептах')),
        )

    def queryset(self, request, queryset):
        queryset = queryset.annotate(
            recipe_count=Count('recipeingredients')
        )
        if self.value() == 'yes':
            return queryset.filter(recipe_count__gt=0)
        if self.value() == 'no':
            return queryset.filter(recipe_count=0)
        return queryset


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit', 'recipes_count')
    search_fields = ('name', 'measurement_unit')
    list_filter = ('measurement_unit', HasRecipesFilter,)
    ordering = ('name',)

    def recipes_count(self, ingredient):
        count = RecipeIngredient.objects.filter(
            ingredient=ingredient
        ).count()
        return count
    recipes_count.short_description = 'Кол-во добавлений рецепты'


# Рецепты
class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 0
    min_num = 1
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
        'image_preview',
        'ingredients_list',
        'favorites_count',
    )
    readonly_fields = ('favorites_count', 'ingredients_list', 'image_preview')
    fieldsets = (
        (None, {
            'fields': ('name', 'author', 'cooking_time', 'image', 'image_preview', 'text')
        }),
        ('Статистика', {
            'fields': ('favorites_count',),
            'description': 'Сколько раз рецепт добавлен в избранное'
        }),
    )
    list_filter = ('author', 'pub_date',)
    search_fields = (
        'name',
        'author__username',
        'author__email',
    )
    ordering = ('-pub_date',)
    inlines = [RecipeIngredientInline]

    @admin.display(description='Ингредиенты')
    @mark_safe
    def ingredients_list(self, recipe):
        """HTML список ингредиентов с единицами измерения"""
        items = []
        products = RecipeIngredient.objects.filter(recipe=recipe)
        for item in products:
            items.append(
                f'<li>{item.ingredient.name} - {item.amount} {item.ingredient.measurement_unit}</li>'
            )
        return f'<ul>{"".join(items)}</ul>' if items else '—'

    @admin.display(description='Превью изображения')
    @mark_safe
    def image_preview(self, recipe):
        """Превью изображения с ссылкой"""
        if recipe.image:
            return f'<a href="{recipe.image.url}" target="_blank"><img src="{recipe.image.url}" style="max-height: 50px;"></a>'
        return '—'

    @admin.display(description='В избранном у ')
    def favorites_count(self, recipe):
        return recipe.in_favorites.count()


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


# Пользователь
@admin.register(User)
class UserWithAvatarAdmin(DjangoUserAdmin):
    model = User
    list_display = ('id',
                    'email',
                    'username',
                    'first_name',
                    'last_name',
                    'avatar_preview',
                    'is_staff',
                    'recipe_count',
                    'subscriptions_count',
                    'subscribers_count',
                    )
    search_fields = ('email', 'username', 'first_name', 'last_name')
    ordering = ('email',)
    readonly_fields = ('avatar_preview',)
    fieldsets = (
        (None, {'fields': ('email',
                           'password')}),
        (('Personal info'), {'fields': ('first_name',
                                        'last_name',
                                        'avatar',
                                        'avatar_preview',)}),
        (('Permissions'), {'fields': ('is_active',
                                      'is_staff',
                                      'is_superuser',
                                      'groups',
                                      'user_permissions')}),
        (('Important dates'), {'fields': ('last_login',
                                          'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email',
                       'username',
                       'first_name',
                       'last_name',
                       'password1',
                       'password2'),
        }),
    )
    list_display_links = ('email',)

    @admin.display(description='Превью аватара')
    @mark_safe
    def avatar_preview(self, user):
        if user.avatar:
            return f'<a href="{user.avatar.url}" target="_blank"><img src="{user.avatar.url}" style="max-height:100px;"></a>'
        return '—'

    @admin.display(description='Количество рецептов')
    def recipe_count(self, user):
        return user.user_recipes.count()

    @admin.display(description='Количество подписок')
    def subscriptions_count(self, user):
        return user.subscriptions.count()

    @admin.display(description='Количество подписчиков')
    def subscribers_count(self, user):
        return user.subscribing.count()


# Подписки
@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'author')
    search_fields = ('user__email', 'author__email')
