from rest_framework.decorators import api_view
from django.shortcuts import redirect


@api_view(['GET'])
def redirect_short_link(request, recipe_id):
    """
    Переход с короткой ссылки на страницу рецепта.
    """
    return redirect(f'/recipes/{recipe_id}/')
