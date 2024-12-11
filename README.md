# Foodgram - Продуктовый Помощник

[![Foodgram Workflow Status](https://github.com/vettspace/foodgram/actions/workflows/foodgram_workflow.yml/badge.svg?branch=main)](https://github.com/vettspace/foodgram/actions/workflows/foodgram_workflow.yml)

## Описание

**Foodgram** - это веб-приложение «Продуктовый помощник», где пользователи могут публиковать рецепты, подписываться на других пользователей, добавлять рецепты в избранное и создавать список покупок ингредиентов для выбранных блюд.

### Основные возможности

- **Регистрация и авторизация** пользователей.
- **Публикация рецептов** с указанием ингредиентов, описанием и фотографией.
- **Подписка на авторов** и просмотр их рецептов в ленте.
- **Добавление рецептов в избранное** для быстрого доступа.
- **Формирование списка покупок** с возможностью скачивания в PDF.

## Технологии

- **Backend**: Python 3.9+, Django, Django REST Framework, PostgreSQL
- **Frontend**: React
- **Управление проектом**: Docker, Docker Compose
- **Веб-сервер**: Nginx
- **Gunicorn** для запуска приложения
- **CI/CD**: GitHub Actions

## Содержание

- [Установка](#установка)
  - [Предварительные требования](#предварительные-требования)
  - [Локальный запуск в Docker](#локальный-запуск-в-docker)
  - [Запуск на удаленном сервере](#запуск-на-удаленном-сервере)
- [Скрипты проекта](#скрипты-проекта)
- [Структура проекта](#структура-проекта)
- [CI/CD](#cicd)
- [Документация API](#документация-api)
- [Автор](#автор)

## Установка

### Предварительные требования

- **Docker** и **Docker Compose**
- **Git**

Убедитесь, что вы установили Docker и Docker Compose на свою систему.

### Локальный запуск в Docker

1. **Склонируйте репозиторий:**

   ```bash
   git clone https://github.com/vettspace/foodgram.git
   ```

2. **Перейдите в директорию проекта:**

   ```bash
   cd foodgram/infra/
   ```

3. **Создайте файл `.env` с переменными окружения:**

   Создайте файл `.env` в директории `infra/` и добавьте в него следующие переменные:

   ```dotenv
   DB_ENGINE=django.db.backends.postgresql
   POSTGRES_DB=foodgram
   POSTGRES_USER=foodgram_user
   POSTGRES_PASSWORD=foodgram_password
   DB_HOST=db
   DB_PORT=5432
   SECRET_KEY=your_secret_key
   ALLOWED_HOSTS=127.0.0.1,localhost
   DEBUG=False
   ```

4. **Запустите Docker Compose:**

   ```bash
   docker-compose up -d --build
   ```

5. **Выполните миграции, соберите статику и создайте суперпользователя:**

   ```bash
   # Применение миграций
   docker-compose exec backend python manage.py migrate
   
   # Сбор статики
   docker-compose exec backend python manage.py collectstatic --no-input
   
   # Создание суперпользователя
   docker-compose exec backend python manage.py createsuperuser
   ```

6. **(Опционально) Загрузите данные в базу данных:**

   ```bash
   # Создание тегов
   docker-compose exec backend python manage.py create_tags
   
   # Загрузка ингредиентов
   docker-compose exec backend python manage.py load_ingredients data/ingredients.json
   
   # Создание тестовых пользователей
   docker-compose exec backend python manage.py create_users
   
   # Создание тестовых рецептов
   docker-compose exec backend python manage.py create_recipes
   ```

7. **Приложение будет доступно по адресу:**

   ```
   http://localhost/
   ```

### Запуск на удаленном сервере

Для развертывания проекта на удаленном сервере с использованием CI/CD выполните следующие шаги:

1. **Настройте переменные окружения в GitHub Secrets:**

   В настройках вашего репозитория на GitHub добавьте следующие Secrets:

   - `DOCKER_USERNAME` и `DOCKER_PASSWORD` для Docker Hub
   - `HOST`, `SSH_USER`, `SSH_KEY`, `SSH_PASSPHRASE` для доступа к серверу по SSH
   - `POSTGRES_USER`, `POSTGRES_PASSWORD`, `DB_NAME` для базы данных
   - `SECRET_KEY` — секретный ключ Django
   - `ALLOWED_HOSTS` — IP или домен вашего сервера
   - `TELEGRAM_TOKEN`, `TELEGRAM_TO` для уведомлений в Telegram (опционально)

2. **Настройте сервер:**

   Установите на сервере Docker и Docker Compose.

3. **GitHub Actions выполнит автоматический деплой при пуше в ветку `main`.**

## Скрипты проекта

### `local_deploy.sh`

Скрипт для локального развертывания проекта. Он:

- Останавливает и удаляет все контейнеры, образы и тома Docker (все данные будут удалены).
- Собирает Docker-образы для фронтенда и бэкенда.
- Запускает Docker Compose для локального развертывания.
- Выполняет миграции, собирает статику, создает тестовые данные и суперпользователя.

**Использование:**

```bash
./local_deploy.sh
```

### Создание тестовых данных

- **`create_tags.py`** — создает предустановленные теги (например, "Завтрак", "Обед", "Ужин").

  ```bash
  docker-compose exec backend python manage.py create_tags
  ```

- **`load_ingredients.py`** — загружает список ингредиентов из файла `ingredients.json`.

  ```bash
  docker-compose exec backend python manage.py load_ingredients data/ingredients.json
  ```

- **`create_users.py`** — создает тестовых пользователей.

  ```bash
  docker-compose exec backend python manage.py create_users
  ```

- **`create_recipes.py`** — создает тестовые рецепты с использованием данных из `test_recipes_data.py` и изображений из `test_pics`.

  ```bash
  docker-compose exec backend python manage.py create_recipes
  ```

## Структура проекта

```
foodgram/
├── backend/
│   ├── Dockerfile
│   ├── manage.py
│   ├── foodgram/          # Настройки Django проекта
│   ├── api/               # Приложение API
│   ├── recipes/           # Приложение рецептов
│   ├── users/             # Приложение пользователей
│   └── data/              # Данные (ингредиенты и т.д.)
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   ├── src/               # Исходный код React
│   └── public/
├── infra/
│   ├── docker-compose.yml
│   ├── docker-local-compose.yml
│   ├── default.conf
│   └── .env               # Переменные окружения
├── docs/
│   ├── openapi-schema.yml
│   └── redoc.html
├── local_deploy.sh
└── README.md
```

## CI/CD

Настроен автоматический деплой с использованием GitHub Actions.

Файл `foodgram_workflow.yml` включает в себя:

- **Тестирование**: запуск flake8.
- **Сборка и публикация образов**: сборка Docker-образов и отправка их на Docker Hub.
- **Деплой на сервер**: автоматическое развёртывание на сервере.
- **Уведомление**: отправка сообщений в Telegram о результате деплоя.

## Документация API

После запуска проекта документация доступна по адресу:

```
http://localhost/api/docs/
```

## Автор

[Виталий Орлов](https://github.com/vettspace)