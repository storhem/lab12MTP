# Платформа онлайн-обучения

**ФИО:** Евланичев Максим Юрьевич  
**Группа:** 221131  
**Лабораторная работа №12, Вариант 7**

[![CI](https://github.com/storhem/lab12MTP/actions/workflows/ci.yml/badge.svg)](https://github.com/storhem/lab12MTP/actions/workflows/ci.yml)
[![Coverage](https://img.shields.io/badge/coverage-90%25%2B-brightgreen)](https://github.com/storhem/lab12MTP/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)

---

## Описание

Веб-приложение "Платформа онлайн-обучения" — REST API для управления курсами, уроками, тестами, записями на курсы и сертификатами. Платформа поддерживает три роли пользователей: студент, преподаватель и администратор.

### Функциональность

- **Аутентификация:** регистрация и вход с использованием JWT-токенов
- **Курсы:** создание, просмотр, обновление, удаление и публикация курсов
- **Уроки:** управление уроками внутри курса с сортировкой по порядку
- **Записи:** запись студентов на курсы, отслеживание прогресса
- **Тесты:** создание тестов с вопросами, прохождение тестов и подсчёт результатов
- **Сертификаты:** автоматическая выдача сертификата при достижении 100% прогресса
- **Аналитика:** топ курсов, прогресс студента, обзор платформы

---

## Технологический стек

| Компонент | Технология |
|-----------|-----------|
| Web Framework | FastAPI 0.115 |
| ORM | SQLAlchemy 2.0 (async) |
| База данных (production) | PostgreSQL 16 (asyncpg) |
| База данных (тесты) | SQLite in-memory (aiosqlite) |
| Миграции | Alembic 1.13 |
| Аутентификация | JWT (python-jose + passlib[bcrypt]) |
| Валидация | Pydantic v2 |
| Тестирование | pytest + pytest-asyncio + httpx |
| Контейнеризация | Docker + docker-compose |

---

## Архитектура

Проект использует слоистую архитектуру:

```
API (routers) → Services (бизнес-логика) → Repositories (доступ к БД) → Models (SQLAlchemy)
```

HTTP-запросы проходят через роутеры FastAPI (валидация и аутентификация), затем через сервисный слой (бизнес-логика), репозиторный слой (CRUD-операции) и ORM-модели до PostgreSQL. Зависимости внедряются через механизм `Depends`.

```
src/app/
├── api/v1/          # Роутеры FastAPI
│   ├── auth.py
│   ├── courses.py
│   ├── lessons.py
│   ├── enrollments.py
│   ├── quizzes.py
│   ├── certificates.py
│   └── analytics.py
├── services/        # Бизнес-логика
├── repositories/    # Работа с БД (CRUD)
├── models/          # SQLAlchemy модели
├── schemas/         # Pydantic схемы
├── core/            # Конфигурация и зависимости
├── database.py      # Подключение к БД
└── main.py          # Точка входа
```

---

## Переменные окружения

Создайте файл `.env` на основе `.env.example`:

```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/learning_platform
SECRET_KEY=your-super-secret-key-change-in-production-minimum-32-chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=learning_platform
```

---

## Запуск через Docker

### 1. Клонировать репозиторий

```bash
git clone https://github.com/storhem/lab12MTP.git
cd lab12MTP
```

### 2. Создать файл .env

```bash
cp .env.example .env
# Отредактируйте .env при необходимости
```

### 3. Запустить сервисы

```bash
docker-compose up --build -d
```

### 4. Проверить работоспособность

```bash
curl http://localhost:8000/health
# {"status": "healthy"}
```

API документация доступна по адресу: http://localhost:8000/docs

### Остановка

```bash
docker-compose down
# Удалить данные:
docker-compose down -v
```

---

## Локальный запуск (без Docker)

### Требования

- Python 3.11+
- PostgreSQL 14+ (или использовать SQLite для разработки)

### Установка

```bash
# Создать виртуальное окружение
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# Установить зависимости
pip install -e ".[dev]"
```

### Настройка PYTHONPATH

```bash
export PYTHONPATH=src  # Linux/Mac
set PYTHONPATH=src     # Windows CMD
$env:PYTHONPATH="src"  # PowerShell
```

### Применить миграции

```bash
alembic upgrade head
```

### Запустить сервер

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## Тестирование

### Запуск тестов

```bash
# Все тесты
pytest

# С отчётом о покрытии
pytest --cov=src --cov-report=html --cov-report=term-missing

# Конкретный файл
pytest tests/test_auth.py -v

# С подробным выводом
pytest -v
```

### Просмотр отчёта о покрытии

```bash
# После запуска с --cov-report=html
open htmlcov/index.html  # Linux/Mac
start htmlcov/index.html # Windows
```

---

## API Endpoints

### Аутентификация

```bash
# Регистрация
POST /api/v1/auth/register
{
  "email": "user@example.com",
  "username": "myuser",
  "full_name": "Иван Иванов",
  "role": "student",
  "password": "securepassword"
}

# Вход
POST /api/v1/auth/login
{
  "email": "user@example.com",
  "password": "securepassword"
}

# Получить текущего пользователя
GET /api/v1/auth/me
Authorization: Bearer <token>
```

### Курсы

```bash
# Список курсов (публичные)
GET /api/v1/courses

# Создать курс (только преподаватель/администратор)
POST /api/v1/courses
Authorization: Bearer <token>
{
  "title": "Python для начинающих",
  "description": "Изучение Python с нуля",
  "level": "beginner",
  "price": 0.0,
  "tags": "python,programming"
}

# Получить курс
GET /api/v1/courses/{id}

# Обновить курс
PUT /api/v1/courses/{id}
Authorization: Bearer <token>
{"title": "Новое название"}

# Опубликовать курс
POST /api/v1/courses/{id}/publish
Authorization: Bearer <token>

# Удалить курс
DELETE /api/v1/courses/{id}
Authorization: Bearer <token>

# Студенты курса
GET /api/v1/courses/{id}/students
Authorization: Bearer <token>

# Уроки курса
GET /api/v1/courses/{id}/lessons
Authorization: Bearer <token>
```

### Уроки

```bash
# Добавить урок
POST /api/v1/lessons/course/{course_id}
Authorization: Bearer <token>
{
  "title": "Введение в Python",
  "content": "Python — высокоуровневый язык...",
  "order_num": 1,
  "duration_minutes": 30,
  "is_published": true
}

# Получить урок
GET /api/v1/lessons/{id}
Authorization: Bearer <token>

# Обновить урок
PUT /api/v1/lessons/{id}
Authorization: Bearer <token>
{"title": "Новое название урока"}

# Удалить урок
DELETE /api/v1/lessons/{id}
Authorization: Bearer <token>
```

### Записи на курс

```bash
# Записаться на курс (только студент)
POST /api/v1/enrollments
Authorization: Bearer <token>
{"course_id": 1}

# Мои записи
GET /api/v1/enrollments/my
Authorization: Bearer <token>

# Обновить прогресс
PUT /api/v1/enrollments/{id}/progress
Authorization: Bearer <token>
{"progress": 75.0}
```

### Тесты

```bash
# Создать тест
POST /api/v1/quizzes
Authorization: Bearer <token>
{
  "course_id": 1,
  "title": "Тест по Python",
  "questions": [
    {
      "question": "Что такое список в Python?",
      "options": ["Тип данных", "Функция", "Модуль", "Класс"],
      "correct_answer": "Тип данных"
    }
  ],
  "passing_score": 70
}

# Пройти тест (только студент)
POST /api/v1/quizzes/{id}/attempt
Authorization: Bearer <token>
{"answers": ["Тип данных"]}

# Результаты попыток
GET /api/v1/quizzes/{id}/results
Authorization: Bearer <token>
```

### Сертификаты

```bash
# Мои сертификаты
GET /api/v1/certificates/my
Authorization: Bearer <token>

# Проверить сертификат (публичный endpoint)
GET /api/v1/certificates/{certificate_number}/verify
```

### Аналитика

```bash
# Топ курсов (публичный)
GET /api/v1/analytics/top-courses?limit=10

# Прогресс студента
GET /api/v1/analytics/student/{student_id}/progress
Authorization: Bearer <token>

# Обзор платформы (только администратор)
GET /api/v1/analytics/overview
Authorization: Bearer <token>
```

---

## Роли пользователей

| Действие | Студент | Преподаватель | Администратор |
|----------|---------|---------------|---------------|
| Просмотр курсов | ✅ | ✅ | ✅ |
| Создание курса | ❌ | ✅ | ✅ |
| Редактирование своего курса | ❌ | ✅ | ✅ |
| Редактирование любого курса | ❌ | ❌ | ✅ |
| Запись на курс | ✅ | ❌ | ✅ |
| Прохождение тестов | ✅ | ❌ | ✅ |
| Создание тестов | ❌ | ✅ | ✅ |
| Просмотр аналитики платформы | ❌ | ❌ | ✅ |

---

## CI/CD

Проект использует GitHub Actions:

- **ci.yml** — запускает тесты при каждом push/PR, проверяет покрытие кода (минимум 90%), публикует отчёт о покрытии в комментарий PR
- **ai_pr_review.yml** — автоматический AI-обзор кода при открытии PR с помощью Google Gemini API

### Настройка секретов

Для работы AI PR Review добавьте секрет `GEMINI_API_KEY` в настройках репозитория.  
Ключ можно получить бесплатно на [aistudio.google.com/apikey](https://aistudio.google.com/apikey).
