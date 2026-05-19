# Social Movie Recommender

Веб-приложение для фильмов, сериалов и аниме с социальной лентой, личной библиотекой и рекомендациями.

## Стек

- `Django + Django REST Framework`
- `PostgreSQL`
- `React + Vite`
- `TMDb API`

## Возможности

- JWT-аутентификация
- Личная библиотека: `watched` / `plan_to_watch`
- Поиск и импорт фильмов из `TMDb`
- Профили и подписки
- Лента активности друзей
- Лайки и комментарии
- Рекомендации
- Каталог с weekly top и жанровыми полками

## Структура

```text
backend/    Django API
frontend/   React client
services/   additional services
```

## Локальный запуск

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

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

### 3. Env

Скопируй шаблон и заполни значения:

```bash
cp .env.example .env
```

## Полезные команды

Заполнить демо-данными:

```bash
cd backend
source .venv/bin/activate
python manage.py seed_demo
```

Обновить cached showcase каталога:

```bash
cd backend
source .venv/bin/activate
python manage.py refresh_movie_showcase --force
```

Запустить тесты:

```bash
cd backend
source .venv/bin/activate
python manage.py test
```

## Docker Deploy

```bash
docker compose up --build -d
```

Сервисы:

- `postgres`
- `backend`
- `frontend`
- `showcase-refresher`

## Demo Login

- `username`: `neonfox`
- `password`: `password123`

## Примечания

- Проект использует только `PostgreSQL`
- Витрина каталога кэшируется в базе и обновляется отдельно
- Все локальные секреты хранятся в `.env`, шаблон лежит в `.env.example`
