import base64

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import redirect

from backend.settings import DEBUG


@api_view(['GET'])
def redirect_short_link(request, encoded_id):
    """
    GET /s/<encoded_id>/  → 302 Redirect на /api/recipes/<decoded_id>/
    """
    try:
        padding = '=' * (4 - (len(encoded_id) % 4))
        raw = base64.urlsafe_b64decode(encoded_id + padding).decode()
        recipe_id = int(raw)
    except (ValueError, TypeError):
        return Response(
            {'error': 'Неправильная короткая ссылка'},
            status=status.HTTP_404_NOT_FOUND
        )
    if DEBUG:
        # Будет кидать на API представление страницы рецепта
        return redirect('recipe-detail', pk=recipe_id)
    else:
        # Будет кидать на фронтенд представление страницы рецепта
        return redirect(f'/recipes/{recipe_id}/')
