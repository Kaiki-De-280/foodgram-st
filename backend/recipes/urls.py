from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import RecipeViewSet

router = DefaultRouter()

router.register(r'recipes', RecipeViewSet, basename='recipe')

urlpatterns = [
    path('', include(router.urls)),
]
