# Foodgram

Сервис для публикации рецептов: пользователи регистрируются, публикуют рецепты, подписываются на авторов, сохраняют избранное и скачивают список покупок.

Адрес: http://foodgram-yatest.sytes.net

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

## Локальный запуск без Docker

```bash
python -m venv backend/venv
backend/venv/Scripts/activate
pip install -r backend/requirements.txt
cp .env.example .env
python backend/manage.py migrate
python backend/manage.py load_ingredients
python backend/manage.py runserver
```

Frontend:

```bash
cd frontend
npm ci
npm start
```

## Docker

Скопируйте переменные окружения и поднимите контейнеры из корня репозитория:

```bash
cp .env.example .env
docker compose up -d --build
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py collectstatic --noinput
docker compose exec backend python manage.py load_ingredients
docker compose exec backend python manage.py createsuperuser
```

Сайт будет доступен на http://localhost

## CI/CD

При пуше в ветку `main` GitHub Actions:

1. запускает flake8 и тесты backend;
2. собирает и пушит образы `foodgram_backend`, `foodgram_frontend`, `foodgram_gateway` в Docker Hub;
3. копирует `docker-compose.production.yml` на сервер и поднимает контейнеры;
4. отправляет сообщение в Telegram.

### Secrets репозитория

Settings → Secrets and variables → Actions:

| Secret | Значение |
| --- | --- |
| `DOCKER_USERNAME` | логин Docker Hub (`vladrozum`) |
| `DOCKER_PASSWORD` | пароль или token Docker Hub |
| `HOST` | `158.160.221.212` |
| `USER` | пользователь SSH на VM |
| `SSH_KEY` | приватный SSH-ключ целиком |
| `TELEGRAM_TO` | id чата |
| `TELEGRAM_TOKEN` | токен бота |

На сервере в каталоге `~/foodgram` должен лежать файл `.env` (в репозиторий его не коммитить). Образы в `docker-compose.production.yml` должны совпадать с `DOCKER_USERNAME`.

Приватный ключ и пароли храните только в Secrets / `.env` на сервере, не в git.
