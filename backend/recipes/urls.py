from django.urls import path

from .views import redirect_short_link

urlpatterns = [
    path(
        's/<str:recipe_id>/',
        redirect_short_link,
        name='short-link-redirect'
    ),
]
