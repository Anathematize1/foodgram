# Foodgram

Сервис для публикации рецептов: пользователи регистрируются, публикуют рецепты, подписываются на авторов, сохраняют избранное и скачивают список покупок.

## Стек

* Python, Django, Django REST Framework, Djoser
* PostgreSQL
* React (готовый frontend из репозитория)
* Nginx, Gunicorn, Docker
* GitHub Actions

## Возможности

* рецепты, ингредиенты и теги
* избранное и список покупок
* подписки на авторов
* регистрация и токен-аутентификация
* короткие ссылки на рецепты
* аватар пользователя

## Локальная разработка

1. Создайте виртуальное окружение и установите зависимости:

```bash
python -m venv venv
venv\Scripts\activate
pip install -r backend/requirements.txt
```

2. Скопируйте `.env.example` в `.env` и задайте `SECRET_KEY`. Для SQLite не указывайте `POSTGRES_DB`.

3. Примените миграции, загрузите ингредиенты и создайте суперпользователя:

```bash
cd backend
python manage.py migrate
python manage.py load_ingredients
python manage.py createsuperuser
python manage.py runserver
```

API: http://127.0.0.1:8000/api/  
Админка: http://127.0.0.1:8000/admin/  
Спецификация: [docs/openapi-schema.yml](docs/openapi-schema.yml) и http://localhost/api/docs/ после запуска nginx.

## Docker

```bash
cp .env.example .env
cd infra
docker compose up --build
```

После старта:

```bash
docker compose exec backend python manage.py createsuperuser
docker compose exec backend python manage.py load_ingredients
```

Миграции и `collectstatic` выполняются при старте контейнера backend.

## Переменные окружения

См. `.env.example`. Основные:

* `SECRET_KEY` — секрет Django, обязателен при `DEBUG=False`
* `DEBUG` — `False` для production
* `ALLOWED_HOSTS` — список хостов через запятую
* `POSTGRES_*` — параметры PostgreSQL
* `CORS_ALLOWED_ORIGINS` — разрешённые origin для API

## Тесты и линтер

```bash
cd backend
python manage.py test api.tests
python -m flake8 . --exclude=venv,migrations
```

Postman-коллекция: `postman_collection/foodgram.postman_collection.json`.

## CI/CD

* `.github/workflows/ci.yml` — lint, тесты и сборка Docker-образа backend.
* `.github/workflows/cd.yml` — после пуша в `main`/`master`: тесты, push образа в Docker Hub и деплой по SSH.

Секреты GitHub: `DOCKER_USERNAME`, `DOCKER_PASSWORD`, `HOST`, `USER`, `SSH_KEY`, `PASSPHRASE`.
