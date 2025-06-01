from django.urls import include, path

from .views import (
    IngredientViewSet,
    RecipeViewSet,
    UserViewSet,
)

from rest_framework.routers import DefaultRouter

router = DefaultRouter()

router.register(r'recipes', RecipeViewSet, basename='recipe')
router.register(r'users', UserViewSet, basename='users')
router.register(r'ingredients', IngredientViewSet, basename='ingredient')

urlpatterns = [

    # Аунтефикация
    path('auth/', include('djoser.urls.authtoken')),

    path('', include(router.urls)),

]
