from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import IngredientViewSet

router = DefaultRouter()

router.register('ingredients', IngredientViewSet, basename='ingredient')

urlpatterns = [
    path('', include(router.urls)),
]
