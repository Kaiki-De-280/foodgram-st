FROM python:3.10-slim

WORKDIR /app

RUN pip install --upgrade pip

RUN pip install gunicorn==20.1.0

COPY requirements.txt .

RUN pip install -r requirements.txt --no-cache-dir

COPY . .

EXPOSE 8000

RUN python manage.py collectstatic --noinput

CMD ["sh", "-c", "python manage.py migrate --noinput && cp -r collected_static/. /backend_static/static/ && gunicorn --bind 0.0.0.0:8000 backend.wsgi"]