# Social Movie Recommender

Социальная платформа для рекомендаций фильмов, сериалов и аниме. Пользователи ведут свои списки, подписываются друг на друга, делятся мнением и получают персональные рекомендации на основе друзей, похожих вкусов и похожего контента.

## Выбранный стек

- `Django + Django REST Framework` как основной backend.
- `PostgreSQL` как основная база данных.
- `React + Vite` как frontend.
- `FastAPI` как отдельный сервис рекомендаций на следующем этапе, когда алгоритмы станут тяжелее и их захочется выносить из основного монолита.

Такой выбор хорошо подходит под твою цель прокачать `Django`: бизнес-логика, auth, ORM, админка и API остаются в одном понятном месте. `FastAPI` здесь не конкурирует с Django, а дополняет его как будущий специализированный сервис.

## Архитектура

```text
frontend (React)
    |
    v
backend (Django REST API)
    |
    +--> PostgreSQL
    |
    +--> TMDb API
    |
    +--> recommendation_api (FastAPI, later stage)
```

## Структура репозитория

```text
backend/
  config/                  Django project settings
  apps/
    accounts/              регистрация, профиль, JWT
    movies/                фильмы, списки, TMDb, ссылки "где смотреть"
    social/                подписки и профили
    feed/                  лента, лайки, комментарии
    recommendations/       серверная логика рекомендаций
frontend/
  src/                     React UI shell
services/
  recommendation_api/      заготовка под FastAPI сервис
```

## Основные доменные сущности

- `User` — пользователь.
- `Movie` — карточка фильма/сериала/аниме, синхронизированная с `TMDb`.
- `UserMovie` — связь пользователя с фильмом: статус, оценка, отзыв.
- `Follow` — подписка на других пользователей.
- `Activity` — события для ленты.
- `ActivityLike` и `ActivityComment` — взаимодействие с лентой.
- `MovieLink` и `LinkVote` — ссылки "где смотреть" и голоса.

## Что уже заложено в каркас

- JWT-аутентификация.
- Кастомная модель пользователя.
- Поиск и импорт фильмов из `TMDb`.
- Кэшируемая витрина каталога из `PostgreSQL`: weekly top и жанровые полки.
- Пользовательская библиотека: `watched` и `plan_to_watch`.
- Социальные подписки и публичные профили.
- Лента активности друзей.
- Лайки и комментарии.
- Базовые рекомендации:
  - популярное среди друзей,
  - советы от похожих пользователей,
  - похожие фильмы по жанрам.
- Отдельная FastAPI-заготовка под вынос recommendation engine.

## Текущий MVP-статус

На текущем этапе в репозитории уже есть рабочая продуктовая база:

- backend-модели, маршруты, сериализаторы и ручные миграции;
- CRUD для пользовательской библиотеки;
- профили, подписки, просмотр списков друзей;
- feed с лайками и комментариями;
- базовый recommendation overview endpoint;
- React-интерфейс в тёмном cyberpunk-стиле;
- demo seed-команда для локального показа.
- daily refresh витрины каталога через отдельную management-команду и docker service.

## API-модули

- `api/auth/`
  - `register/`
  - `me/`
  - `token/`
  - `token/refresh/`
- `api/movies/`
  - локальный список и детали
  - cached showcase для каталога
  - поиск в `TMDb`
  - импорт фильма из `TMDb`
  - библиотека пользователя
  - ссылки и голосование
- `api/social/`
  - профиль
  - follow / unfollow
  - followers / following
- `api/feed/`
  - лента активности
  - лайк
  - комментарии
- `api/recommendations/`
  - обзор рекомендаций для текущего пользователя

## Почему не Flask

`Flask` хорош для небольших сервисов, но под твои требования здесь слабее стартовая база:

- меньше встроенных возможностей для auth, admin и ORM-связей;
- больше ручной сборки вокруг пользователей, feed и social graph;
- хуже подходит, если цель именно углубиться в `Django`.

Поэтому для этого проекта логичнее:

1. Основной продукт делать на `Django`.
2. `FastAPI` подключать позже только там, где реально нужен отдельный быстрый сервис.

## Этапы разработки

### Этап 1. MVP

- регистрация и вход;
- импорт фильмов из `TMDb`;
- добавление в `watched` и `plan_to_watch`;
- оценка фильмов.

### Этап 2. Social

- подписки;
- профили пользователей;
- просмотр списков друзей.

### Этап 3. Feed

- события активности;
- лента друзей;
- ограничение и сортировка.

### Этап 4. Recommendations

- рекомендации по друзьям;
- похожие пользователи;
- похожие фильмы;
- при необходимости вынос логики в `FastAPI`.

### Этап 5. Engagement

- лайки;
- комментарии;
- ссылки "где смотреть" и голосование.

### Этап 6. UI polish

- полноценный React-интерфейс;
- адаптивность;
- улучшение UX ленты и профилей.

## Быстрый старт

### 1. Backend

```bash
docker compose up -d postgres
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Если у тебя уже есть данные в старом `SQLite`, перенеси их в `PostgreSQL` так:

```bash
cd backend
source .venv/bin/activate
python manage.py import_legacy_sqlite --source db.sqlite3
```

Если старые данные не нужны и хочется просто получить демо-набор для показа:

```bash
cd backend
source .venv/bin/activate
python manage.py seed_demo
```

Обновить cached-витрину каталога вручную:

```bash
cd backend
source .venv/bin/activate
python manage.py refresh_movie_showcase
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

### 3. Переменные окружения

Смотри `.env.example`.

Backend теперь настроен только на `PostgreSQL`. Достаточно поднять контейнер из `docker-compose.yml` и держать значения `POSTGRES_*` синхронными с `.env`.

Если раньше ты запускал проект через старый `SQLite`-файл, он больше не используется. Для новой базы просто выполни миграции и при необходимости снова вызови `python manage.py seed_demo`.

## Production / Server Deploy

Проект теперь подготовлен под деплой через `Docker Compose`:

- `postgres` — основная база данных;
- `backend` — `Django + gunicorn`;
- `frontend` — `nginx`, который раздаёт собранный `React` и проксирует `/api`, `/admin`, `/health` в backend.
- `showcase-refresher` — отдельный backend worker, который раз в сутки обновляет weekly top и жанровые полки каталога.

### 1. Подготовь переменные окружения

Скопируй шаблон и заполни свои значения:

```bash
cp .env.example .env
```

Минимум, что нужно поменять перед сервером:

- `DJANGO_SECRET_KEY`
- `DJANGO_ALLOWED_HOSTS`
- `CORS_ALLOWED_ORIGINS`
- `CSRF_TRUSTED_ORIGINS`
- `POSTGRES_PASSWORD`
- `TMDB_API_KEY`

### 2. Подними стек на сервере

```bash
docker compose up --build -d
```

После этого сайт будет доступен на порту `80`, если не менял `FRONTEND_PORT`.

### 3. Полезные команды после деплоя

Создать администратора:

```bash
docker compose exec backend python manage.py createsuperuser
```

Засеять demo-данные:

```bash
docker compose exec backend python manage.py seed_demo
```

Импортировать данные из старого `SQLite`:

```bash
docker compose exec backend python manage.py import_legacy_sqlite --source db.sqlite3
```

Если целевая Postgres-база уже содержит данные и ты сознательно хочешь её перезаписать:

```bash
docker compose exec backend python manage.py import_legacy_sqlite --source db.sqlite3 --flush-target
```

### 4. Тесты

```bash
cd backend
source .venv/bin/activate
python manage.py test
```

### 5. Demo-пользователь

После `python manage.py seed_demo` можно войти:

- `username`: `neonfox`
- `password`: `password123`

## Что стоит сделать следующим шагом

Если хочешь, следующим сообщением я могу пойти в один из трёх практичных сценариев:

1. добить production-ready слой: pagination, permissions, logging, CI и Docker для всего стека;
2. углубить recommendation engine и вынести его в `FastAPI`;
3. добавить более полный social UX: уведомления, review threads, richer movie pages.
