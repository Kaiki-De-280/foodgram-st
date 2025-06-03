#!/bin/sh

set -e

python manage.py migrate --noinput

cp -r collected_static/. /backend_static/static/

if [ "$(python manage.py shell -c "from recipes.models import Ingredient; print(Ingredient.objects.exists())")" = "False" ]; then
    echo "Загрузка fixtures/products.json"
    python manage.py loaddata ingredients.json
else
    echo "Fixtures уже загружены"
fi

exec "$@"