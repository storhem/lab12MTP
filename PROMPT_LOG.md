# PROMPT_LOG.md — Журнал AI-ассистированной разработки

**Проект:** Платформа онлайн-обучения  
**ФИО:** Евланичев Максим Юрьевич  
**Группа:** 221131  
**ЛР №12, Вариант 7 (повышенная сложность)**  
**Инструмент:** Claude Code (claude-sonnet-4-6)

---

## Задание В1 — Создание полноценного веб-приложения

### Промпт 0.1 — Инициализация проекта

**Инструмент:** Claude Code  
**Дата:** 09.05.2026

**Промпт:**
```
Мне нужно создать структуру Python-проекта для платформы онлайн-обучения.
Предметная область: курсы, уроки, студенты, тесты, сертификаты.
Используй src-layout (код в папке src/), pyproject.toml без setup.py.
Нужен .gitignore для Python проекта и .env.example с переменными для PostgreSQL и JWT.
Какие зависимости нужны для FastAPI + SQLAlchemy 2.0 async + PostgreSQL?
```

**Результат ИИ:**
```
Для твоего стека нужны:
- fastapi, uvicorn[standard] — веб-фреймворк
- sqlalchemy[asyncio], asyncpg — async ORM + PostgreSQL драйвер
- aiosqlite — для SQLite в тестах
- alembic — миграции БД
- python-jose[cryptography], passlib[bcrypt] — JWT + хеширование паролей
- pydantic-settings, pydantic[email] — конфигурация и валидация
- python-multipart — для form-data (логин через OAuth2)
```

Создан `pyproject.toml` с фиксированными версиями, src-layout конфигурацией и dev-зависимостями для тестирования.

**Что пришлось исправлять:** ИИ изначально предложил `setup.cfg` вместо `pyproject.toml` — попросил переделать на современный формат.

**Итого промпт 0.1:**
- Количество итераций: 2
- Что исправлял вручную: ничего
- Время: ~15 мин

---

### Промпт 1.1 — Модели данных (User, Course)

**Инструмент:** Claude Code  
**Дата:** 09.05.2026

**Промпт:**
```
Создай SQLAlchemy 2.0 модели с Mapped[] типизацией для платформы обучения.
Начнём с основных сущностей:

1. User — id, email (unique, indexed), username (unique), hashed_password, 
   full_name, role (enum: student/instructor/admin), is_active (default True), 
   created_at (datetime, server_default=now())

2. Course — id, title, description (text), instructor_id (FK→users, не nullable), 
   level (enum: beginner/intermediate/advanced), price (float, default 0.0), 
   is_published (bool, default False), tags (str, nullable), created_at

Используй DeclarativeBase из database.py, relationship с back_populates, 
lazy="selectin" для связей.
```

**Результат ИИ:**
- Созданы модели с Mapped[] аннотациями в стиле SQLAlchemy 2.0
- Enum-классы наследуются от str и Enum одновременно (для совместимости с Pydantic)
- relationship настроены с back_populates и lazy="selectin"

**Проблема:** ИИ использовал `Column()` в старом стиле для нескольких полей — попросил переделать полностью на `mapped_column()`.

**Промпт исправления:**
```
Перепиши User и Course модели полностью используя только Mapped[] и mapped_column().
Ни одного Column() не должно остаться — это SQLAlchemy 1.x стиль.
```

**Итого промпт 1.1:**
- Количество итераций: 2
- Что исправлял вручную: ничего
- Время: ~20 мин

---

### Промпт 1.2 — Модели данных (Lesson, Enrollment, Quiz, Certificate)

**Инструмент:** Claude Code  
**Дата:** 09.05.2026

**Промпт:**
```
Продолжи создавать модели данных. Нужны ещё 5 моделей:

3. Lesson — id, course_id (FK→courses), title, content (text), 
   order_num (int, сортировка внутри курса), duration_minutes (int), 
   is_published (bool, True), created_at

4. Enrollment — id, student_id (FK→users), course_id (FK→courses),
   enrolled_at, completed_at (nullable datetime), progress (float, default 0.0),
   is_active (bool, True)
   UniqueConstraint(student_id, course_id)

5. Quiz — id, course_id (FK→courses), lesson_id (FK→lessons, nullable),
   title, questions (JSON — список вопросов), passing_score (int, 0-100), created_at

6. QuizAttempt — id, quiz_id (FK→quizzes), student_id (FK→users),
   score (float), passed (bool), attempted_at

7. Certificate — id, student_id (FK→users), course_id (FK→courses), 
   enrollment_id (FK→enrollments, unique — один сертификат на запись),
   certificate_number (str, unique), issued_at

Все модели добавь в __init__.py чтобы Alembic их видел.
```

**Результат ИИ:**
- Все 5 моделей созданы с правильными FK и ограничениями
- UniqueConstraint для Enrollment (student_id, course_id)
- unique=True для Certificate.enrollment_id (идемпотентность)
- JSON тип для Quiz.questions

**Что пришлось исправлять:** relationship из Certificate обратно в Enrollment был объявлен неправильно — исправил вручную `back_populates` имя.

**Итого промпт 1.2:**
- Количество итераций: 1
- Что исправлял вручную: back_populates в Certificate.enrollment
- Время: ~25 мин

---

### Промпт 1.3 — Конфигурация и безопасность

**Инструмент:** Claude Code  
**Дата:** 09.05.2026

**Промпт:**
```
Создай два модуля для core:

1. config.py — pydantic-settings BaseSettings с полями:
   DATABASE_URL, SECRET_KEY, ALGORITHM (HS256), ACCESS_TOKEN_EXPIRE_MINUTES (30)
   Читать из .env файла, extra="ignore" для лишних переменных

2. security.py — утилиты JWT и паролей:
   - verify_password(plain, hashed) → bool
   - get_password_hash(password) → str
   - create_access_token(data, expires_delta) → str
   - decode_token(token) → dict (raises HTTPException 401 если невалиден)
   
Используй passlib CryptContext с bcrypt, python-jose для JWT.
```

**Результат ИИ:**
- Настроен pydantic-settings с автозагрузкой из .env
- passlib CryptContext(schemes=["bcrypt"])
- python-jose для encode/decode JWT с exp claim

**Итого промпт 1.3:**
- Количество итераций: 1
- Что исправлял вручную: ничего
- Время: ~10 мин

---

### Промпт 1.4 — Слой репозиториев

**Инструмент:** Claude Code  
**Дата:** 09.05.2026

**Промпт:**
```
Создай generic BaseRepository[ModelType] с TypeVar для async CRUD:

class BaseRepository(Generic[ModelType]):
    def __init__(self, session: AsyncSession, model: type[ModelType])
    async def get(self, id: int) → ModelType | None
    async def get_multi(self, skip=0, limit=100, **filters) → list[ModelType]
    async def create(self, **kwargs) → ModelType
    async def update(self, obj, **kwargs) → ModelType
    async def delete(self, obj) → None
    async def count(**filters) → int

Потом создай специфические репозитории наследуясь от Base:
- UserRepository: get_by_email, get_by_username
- CourseRepository: get_by_instructor, get_published
- LessonRepository: get_by_course, get_published_by_course, get_by_course_ordered
- EnrollmentRepository: get_by_student, get_by_student_and_course, update_progress (автоматически устанавливает completed_at при progress=100)
- QuizRepository: get_by_course, get_by_lesson
- QuizAttemptRepository: get_by_student_and_quiz
- CertificateRepository: get_by_student, get_by_number, get_by_enrollment
```

**Результат ИИ:**
- Generic BaseRepository с TypeVar и Generic
- select() + where() для фильтрации
- EnrollmentRepository.update_progress устанавливает completed_at=datetime.utcnow() при 100%

**Проблема:** get_multi() игнорировал **filters — они были переданы как kwargs но не применялись к запросу.

**Промпт исправления:**
```
В BaseRepository.get_multi() filters не применяются к SQL-запросу.
Нужно сделать: for key, value in filters.items(): stmt = stmt.where(getattr(self.model, key) == value)
Но это упадёт если поля нет в модели. Добавь проверку hasattr.
```

**Итого промпт 1.4:**
- Количество итераций: 2
- Что исправлял вручную: ничего
- Время: ~30 мин

---

### Промпт 1.5 — Сервисы: Auth и Courses

**Инструмент:** Claude Code  
**Дата:** 09.05.2026

**Промпт:**
```
Создай сервис аутентификации (services/auth.py):

async def register(session, user_create: UserCreate) → User:
    - Проверить уникальность email (400 если занят)
    - Проверить уникальность username (400 если занят) 
    - Захешировать пароль через get_password_hash
    - Создать пользователя через UserRepository

async def login(session, email, password) → dict с access_token:
    - Найти по email (401 если не найден)
    - verify_password (401 если неверный)
    - create_access_token с sub=str(user.id)

async def get_current_user(session, token) → User:
    - decode_token → получить sub
    - Найти пользователя по id (401 если не найден)

def require_roles(*roles) → Callable:
    - Dependency factory
    - Admin всегда проходит независимо от roles
    - 403 если роль не совпадает

Также создай сервис courses (services/courses.py):
- create_course: проверить что instructor — роль instructor/admin
- get_course: 404 если не найден
- update_course: проверить владение (только свой курс для instructor)
- delete_course: то же
- publish_course / unpublish_course: переключение is_published
```

**Результат ИИ:**
- register, login, get_current_user реализованы
- require_roles возвращает async функцию-зависимость через замыкание
- CourseService с проверками владения

**Проблема:** require_roles не проверял admin при вложенном вызове — если admin вызывал эндпоинт с require_roles("instructor"), он получал 403.

**Промпт исправления:**
```
В require_roles нужно добавить проверку: if current_user.role == UserRole.admin: return current_user
Это должно быть до проверки roles, чтобы admin всегда проходил.
```

**Итого промпт 1.5:**
- Количество итераций: 2
- Что исправлял вручную: ничего
- Время: ~25 мин

---

### Промпт 1.6 — Сервисы: Lessons, Enrollments, Quizzes

**Инструмент:** Claude Code  
**Дата:** 10.05.2026

**Промпт:**
```
Создай сервисы для уроков и записей:

LessonService (services/lessons.py):
- create_lesson(course_id, lesson_create, current_user) → проверить что курс существует и belongs to instructor
- list_lessons(course_id, current_user) → если student — только published, иначе все
- update_lesson / delete_lesson → проверка владения через курс

EnrollmentService (services/enrollments.py):  
- enroll(student_id, course_id) → проверить что курс published (400 если нет), 
  проверить дублирование (400 "Already enrolled"), создать Enrollment
- update_progress(enrollment_id, student_id, progress) → обновить прогресс,
  если progress >= 100: вызвать issue_certificate (идемпотентно)
- get_my_enrollments(student_id) → список записей студента

QuizService (services/quizzes.py):
- create_quiz(course_id, quiz_create, current_user) → проверить владение курсом
- submit_attempt(quiz_id, student_id, answers) → подсчитать score:
  answers — список {question_id, answer}, в questions JSON хранится {id, question, options, correct_answer}
  score = (correct / total) * 100, passed = score >= passing_score
  Создать QuizAttempt и вернуть результат
```

**Результат ИИ:**
- list_lessons корректно разделяет по роли
- submit_attempt подсчитывает score через сравнение с correct_answer в JSON
- update_progress вызывает CertificateService.issue_certificate

**Итого промпт 1.6:**
- Количество итераций: 1
- Что исправлял вручную: ничего
- Время: ~20 мин

---

### Промпт 1.7 — Сервисы: Analytics и Certificates

**Инструмент:** Claude Code  
**Дата:** 10.05.2026

**Промпт:**
```
Создай два оставшихся сервиса:

CertificateService (services/certificates.py):
- issue_certificate(student_id, course_id, enrollment_id) → идемпотентно:
  сначала проверить get_by_enrollment(enrollment_id), если есть — вернуть существующий
  иначе создать с certificate_number = f"CERT-{uuid4().hex[:12].upper()}"
- get_my_certificates(student_id) → список сертификатов
- verify_by_number(certificate_number) → 404 если не найден

AnalyticsService (services/analytics.py):
- top_courses(limit=10) → курсы с наибольшим числом записей
  SQL: SELECT course_id, COUNT(*) as count FROM enrollments GROUP BY course_id ORDER BY count DESC
- student_progress(student_id) → список курсов с прогрессом студента
- platform_overview() → общая статистика: total_users, total_courses, total_enrollments, 
  total_certificates (только для admin)
```

**Результат ИИ:**
- CertificateService.issue_certificate идемпотентна
- AnalyticsService использует select() с func.count() для агрегации
- platform_overview возвращает словарь со статистикой

**Проблема:** ИИ использовал session.execute(text("SELECT...")) вместо ORM запросов — попросил переписать.

**Промпт исправления:**
```
Перепиши top_courses используя SQLAlchemy ORM:
from sqlalchemy import func, select
stmt = select(Enrollment.course_id, func.count().label("count")).group_by(Enrollment.course_id).order_by(desc("count")).limit(limit)
```

**Итого промпт 1.7:**
- Количество итераций: 2
- Что исправлял вручную: ничего
- Время: ~20 мин

---

### Промпт 1.8 — API роутеры

**Инструмент:** Claude Code  
**Дата:** 10.05.2026

**Промпт:**
```
Создай FastAPI роутеры для всех сущностей. Используй Annotated + Depends для DI.

auth.py (prefix="/auth"):
- POST /register → 201
- POST /login (OAuth2PasswordRequestForm) → 200 + token
- GET /me → текущий пользователь

courses.py (prefix="/courses"):
- GET / → список опубликованных курсов (публичный)
- POST / → создать курс (instructor/admin, 201)
- GET /{id} → один курс
- PUT /{id} → обновить (владелец/admin)
- DELETE /{id} → удалить (владелец/admin)
- POST /{id}/publish → опубликовать
- GET /{id}/lessons → уроки курса (с учётом роли)

lessons.py, enrollments.py, quizzes.py, certificates.py, analytics.py — аналогично.

main.py: подключи все роутеры, добавь CORS middleware, health check GET /health.
```

**Результат ИИ:**
- Все роутеры созданы, подключены в main.py
- OAuth2PasswordRequestForm для /login (стандартный форм)
- CORS middleware разрешает все origins (для разработки)
- GET /health → {"status": "ok"}

**Проблема 1:** GET /courses/ требовал авторизацию — студенты не могли просматривать каталог.
**Промпт:** "Сделай GET /courses/ публичным эндпоинтом без авторизации"

**Проблема 2:** POST /auth/register возвращал 200 вместо 201.
**Промпт:** "Все POST-эндпоинты для создания ресурсов должны возвращать status_code=201"

**Итого промпт 1.8:**
- Количество итераций: 3
- Что исправлял вручную: ничего
- Время: ~35 мин

---

### Промпт 1.9 — Alembic миграция

**Инструмент:** Claude Code  
**Дата:** 10.05.2026

**Промпт:**
```
Создай Alembic конфигурацию для async SQLAlchemy:

1. alembic.ini — стандартный конфиг, sqlalchemy.url будет из env.py

2. alembic/env.py — async вариант:
   - Импортировать Base из app.database и все модели из app.models
   - Использовать async engine через run_async_main()
   - Брать URL из settings.DATABASE_URL

3. alembic/versions/001_initial_schema.py — полная начальная миграция:
   создать все таблицы: users, courses, lessons, enrollments, quizzes, 
   quiz_attempts, certificates со всеми FK, UniqueConstraint, индексами
```

**Результат ИИ:**
- alembic/env.py с asyncio.run() для async подключения
- Миграция создаёт все 7 таблиц с правильными типами
- Индексы для часто запрашиваемых полей (email, course_id, student_id)

**Итого промпт 1.9:**
- Количество итераций: 1
- Что исправлял вручную: ничего
- Время: ~15 мин

---

### Промпт 1.10 — Docker и docker-compose

**Инструмент:** Claude Code  
**Дата:** 10.05.2026

**Промпт:**
```
Создай Docker конфигурацию:

Dockerfile:
- FROM python:3.11-slim
- WORKDIR /app
- Скопировать pyproject.toml, установить pip install -e .
- Скопировать src/, alembic/, alembic.ini
- ENV PYTHONPATH=/app/src (важно для src-layout!)
- CMD: alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000

docker-compose.yml:
- postgres:16-alpine с healthcheck (pg_isready)
- app: build из Dockerfile, depends_on: {postgres: condition: service_healthy}
- Переменные из .env файла
- Volumes для данных PostgreSQL
```

**Результат ИИ:**
- Dockerfile создан, PYTHONPATH установлен
- docker-compose с healthcheck для postgres
- Volumes: postgres_data для персистентности

**Проблема:** В CMD не было `&&` между alembic и uvicorn — нужно через shell форму.

**Промпт исправления:**
```
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
```

**Итого промпт 1.10:**
- Количество итераций: 2
- Что исправлял вручную: ничего
- Время: ~15 мин

---

## Задание В2 — Code Review сгенерированного кода

### Промпт 2.1 — Первичный code review

**Инструмент:** Claude Code  
**Дата:** 11.05.2026

**Промпт:**
```
Проведи критический code review следующих файлов проекта:
- src/app/repositories/base.py
- src/app/services/enrollments.py  
- src/app/api/v1/courses.py
- src/app/api/v1/quizzes.py
- src/app/schemas/course.py

Найди: логические ошибки, уязвимости безопасности, проблемы производительности,
нарушения REST-конвенций, отсутствие валидации, нарушения стиля PEP8.
Для каждой проблемы: опиши проблему и предложи исправление.
```

**Результат ИИ — обнаружены проблемы:**

#### Проблема 2.1 — POST-эндпоинты возвращают 200 вместо 201

**Что сгенерировал ИИ:**
```python
@router.post("/")
async def create_course(...) -> CourseResponse:  # status_code не указан → 200
```

**В чём проблема:** REST-конвенция: создание ресурса → 201 Created.

**Как исправил:**
```python
@router.post("/", status_code=201)
async def create_course(...) -> CourseResponse:
```

Исправлено во всех POST-эндпоинтах: /auth/register, /courses, /lessons, /enrollments, /quizzes, /quizzes/{id}/attempt.

---

#### Проблема 2.2 — Отрицательная цена курса проходила валидацию

**Что сгенерировал ИИ:**
```python
class CourseCreate(BaseModel):
    price: float = 0.0  # нет ограничения снизу
```

**В чём проблема:** Курс с price=-100 создавался без ошибки.

**Как исправил:**
```python
from pydantic import Field
price: float = Field(default=0.0, ge=0.0)
```

---

#### Проблема 2.3 — Race condition при выдаче сертификата

**Что сгенерировал ИИ:**
```python
async def update_progress(self, enrollment_id, student_id, progress):
    enrollment = await self.get(enrollment_id)
    enrollment = await repo.update(enrollment, progress=progress)
    if progress >= 100:
        await cert_service.issue_certificate(...)  # вызывается каждый раз!
```

**В чём проблема:** При двух одновременных запросах обновления прогресса до 100% могут быть созданы два сертификата.

**Как исправил:** В `CertificateService.issue_certificate()` добавлена проверка перед созданием:
```python
existing = await cert_repo.get_by_enrollment(enrollment_id)
if existing:
    return existing  # идемпотентность
```
Также в БД установлен `unique=True` для `enrollment_id` как дополнительная защита.

---

#### Проблема 2.4 — Студент видел неопубликованные уроки

**Что сгенерировал ИИ:**
```python
@router.get("/course/{course_id}")
async def list_lessons(course_id: int, session: ..., current_user: ...):
    return await lesson_service.list_lessons(course_id, current_user)
    # в сервисе не было разделения по роли!
```

**В чём проблема:** Студент мог получить уроки которые ещё не опубликованы.

**Как исправил:** В `LessonService.list_lessons()`:
```python
if current_user.role == UserRole.student:
    return await lesson_repo.get_published_by_course(course_id)
return await lesson_repo.get_by_course_ordered(course_id)
```

---

#### Проблема 2.5 — Отсутствие PYTHONPATH в Dockerfile

**Что сгенерировал ИИ:**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY src/ ./src/
CMD ["uvicorn", "app.main:app", ...]
# ModuleNotFoundError: No module named 'app' при запуске!
```

**В чём проблема:** При src-layout Python не знает где искать пакет `app`.

**Как исправил:**
```dockerfile
ENV PYTHONPATH=/app/src
```

---

#### Проблема 2.6 — Инструктор мог изменить чужой курс

**Что сгенерировал ИИ:**
```python
async def update_course(course_id, update_data, current_user):
    course = await course_repo.get(course_id)
    if not course:
        raise HTTPException(404)
    return await course_repo.update(course, **update_data)
    # нет проверки instructor_id == current_user.id!
```

**В чём проблема:** Любой instructor мог изменить курс другого instructor.

**Как исправил:**
```python
if current_user.role != UserRole.admin and course.instructor_id != current_user.id:
    raise HTTPException(403, "Not your course")
```

### Итого по заданию 2:

- Найдено проблем: 6
- Исправлено: 6
- Критических уязвимостей (безопасность): 2 (race condition сертификата, изменение чужого курса)
- Нарушения REST-конвенций: 2 (статус-коды, валидация цены)
- Проблемы конфигурации: 1 (PYTHONPATH)
- Логические ошибки: 1 (видимость уроков)

---

## Задание В4 — Интеграция ИИ в CI/CD

### Промпт 4.1 — GitHub Actions CI pipeline

**Инструмент:** Claude Code  
**Дата:** 11.05.2026

**Промпт:**
```
Создай GitHub Actions workflow для CI:
- Триггер: push и pull_request на ветки main, master, develop
- Python 3.11 через actions/setup-python@v5
- Кэширование pip зависимостей через actions/cache@v4
- Установка: pip install -e ".[dev]"
- Запуск тестов: pytest --cov=src --cov-report=xml --cov-fail-under=90
- Загрузка HTML отчёта покрытия как артефакт через actions/upload-artifact@v4
- Fail если покрытие < 90%
```

**Результат ИИ:**
- `.github/workflows/ci.yml` создан
- Кэш по хешу `pyproject.toml`
- `--cov-fail-under=90` для проверки минимального порога

**Итого промпт 4.1:**
- Количество итераций: 1
- Что исправлял вручную: ничего
- Время: ~10 мин

---

### Промпт 4.2 — AI PR Review workflow

**Инструмент:** Claude Code  
**Дата:** 11.05.2026

**Промпт:**
```
Создай GitHub Actions workflow для автоматического AI code review в PR:
- Триггер: pull_request (opened, synchronize, reopened)
- Получить git diff изменений: git diff ${{ github.event.pull_request.base.sha }} HEAD
- Ограничить diff до 4000 символов чтобы не превысить лимит API
- Отправить запрос к Anthropic API (claude-3-5-sonnet-20241022):
  роль: code reviewer, проверить: баги, уязвимости, стиль
- Опубликовать ответ как комментарий к PR через GitHub API
  POST /repos/{owner}/{repo}/issues/{pr_number}/comments
- Использовать secrets: ANTHROPIC_API_KEY, GITHUB_TOKEN (встроенный)
```

**Результат ИИ:**
- Workflow создан с curl запросами к Anthropic API
- Python3 используется для JSON-сериализации и парсинга ответа
- GITHUB_TOKEN — встроенный секрет GitHub Actions

**Проблема:** ИИ поставил `anthropic.claude-3-5-sonnet-20241022` как model ID — нужно было проверить актуальное название.

**Промпт исправления:**
```
Проверь актуальный model ID для Anthropic API Claude 3.5 Sonnet.
Правильно: claude-3-5-sonnet-20241022 (без "anthropic." в начале)
```

**Итого промпт 4.2:**
- Количество итераций: 2
- Что исправлял вручную: ничего
- Время: ~20 мин

---

## Задание В7 — Генерация unit-тестов

### Промпт 7.1 — Тестовая инфраструктура (conftest.py)

**Инструмент:** Claude Code  
**Дата:** 11.05.2026

**Промпт:**
```
Создай conftest.py для pytest с SQLAlchemy async + FastAPI:

- Используй SQLite in-memory через aiosqlite (url: "sqlite+aiosqlite:///:memory:")
  Не PostgreSQL — тесты должны работать без Docker
- create_all() через engine для создания схемы
- Override dependency get_session через app.dependency_overrides
- Fixtures (scope нужно продумать аккуратно):
  - setup_database: scope="session", создаёт таблицы
  - db_session: scope="function", новая сессия на каждый тест
  - client: AsyncClient(app, base_url="http://test") через ASGITransport
  - test_student, test_instructor, test_admin: scope="function",
    регистрируют пользователей через API
  
Helper: async def get_auth_headers(client, email, password) → {"Authorization": "Bearer ..."}

ВАЖНО: каждый тест должен быть изолирован — использовать уникальные email/username
через uuid4() чтобы не было конфликтов между тестами.
```

**Результат ИИ:**
- scope="session" для setup_database (создаётся один раз)
- app.dependency_overrides для подмены get_session
- ASGITransport для интеграционных тестов без реального сервера
- uuid4() суффиксы в фикстурах пользователей

**Проблема:** При использовании scope="session" для db_session и scope="function" для client возникал конфликт event loop.

**Промпт исправления:**
```
Возникает ошибка: "Task attached to a different loop".
Это из-за смешивания scope="session" и scope="function" с asyncio.
Как правильно настроить event loop для pytest-asyncio?
Добавь в pyproject.toml: asyncio_mode = "auto"
И все фикстуры сделай scope="function" кроме setup_database.
```

**Итого промпт 7.1:**
- Количество итераций: 3
- Что исправлял вручную: ничего
- Время: ~30 мин

---

### Промпт 7.2 — Тесты аутентификации

**Инструмент:** Claude Code  
**Дата:** 12.05.2026

**Промпт:**
```
Напиши полные тесты для auth эндпоинтов (tests/test_auth.py):

Позитивные сценарии:
- POST /auth/register → 201, проверить email/username/role в ответе
- POST /auth/login → 200, access_token присутствует в ответе
- GET /auth/me с токеном → 200, данные соответствуют

Негативные сценарии:
- Дублирование email при регистрации → 400
- Дублирование username при регистрации → 400  
- Неверный пароль при логине → 401
- GET /auth/me без токена → 401
- GET /auth/me с невалидным токеном → 401
- Регистрация с паролем короче 6 символов → 422 (pydantic validation)

Каждый тест изолирован через уникальные email/username.
```

**Результат ИИ:** 9 тест-кейсов, все покрывают граничные случаи.

**Итого промпт 7.2:**
- Количество итераций: 1
- Что исправлял вручную: ничего
- Время: ~15 мин

---

### Промпт 7.3 — Тесты курсов и уроков

**Инструмент:** Claude Code  
**Дата:** 12.05.2026

**Промпт:**
```
Напиши тесты для courses и lessons (test_courses.py, test_lessons.py):

Courses:
- Создание курса инструктором → 201
- Создание курса студентом → 403
- Получение списка курсов (публичный) → 200
- Получение курса по id → 200
- Обновление курса владельцем → 200
- Обновление чужого курса → 403
- Удаление курса → 204
- Публикация курса → 200, is_published=True
- Запись на неопубликованный курс → 400

Lessons:
- Добавление урока к курсу инструктором → 201
- Студент видит только опубликованные уроки
- Инструктор видит все уроки
- Обновление урока → 200
- Удаление урока → 204
- Студент не может добавлять уроки → 403
```

**Результат ИИ:** 15 тест-кейсов.

**Итого промпт 7.3:**
- Количество итераций: 1
- Что исправлял вручную: ничего
- Время: ~20 мин

---

### Промпт 7.4 — Тесты записей, тестов и сертификатов

**Инструмент:** Claude Code  
**Дата:** 12.05.2026

**Промпт:**
```
Напиши e2e тесты для enrollment → quiz → certificate flow:

Enrollments:
- Запись на опубликованный курс → 201
- Дублирующаяся запись → 400
- Обновление прогресса до 50% → 200, progress=50.0
- Обновление прогресса до 100% → автовыдача сертификата
- Прогресс > 100 → 422

Quizzes:
- Создание теста с вопросами → 201
- Попытка теста с правильными ответами → passed=True
- Попытка теста с неверными ответами → passed=False
- Получение результата попытки → 200

Certificates:
- Сертификат создаётся при progress=100
- Повторный progress=100 не создаёт второй сертификат
- Верификация по номеру → 200 с данными
- Верификация несуществующего → 404
- GET /certificates/my → список сертификатов студента

Analytics:
- GET /analytics/top-courses → 200, список курсов с count
- GET /analytics/overview (admin) → 200
- GET /analytics/overview (student) → 403
```

**Результат ИИ:** 19 тест-кейсов покрывающих полный флоу.

**Итого промпт 7.4:**
- Количество итераций: 1
- Что исправлял вручную: ничего
- Время: ~25 мин

---

### Результаты покрытия тестами

Запуск: `pytest --cov=src --cov-report=term-missing`

```
Module                              Stmts   Miss  Cover
-------------------------------------------------------
src/app/api/v1/analytics.py           21      2    90%
src/app/api/v1/auth.py                24      0   100%
src/app/api/v1/certificates.py        12      0   100%
src/app/api/v1/courses.py             43      3    93%
src/app/api/v1/enrollments.py         19      0   100%
src/app/api/v1/lessons.py             26      0   100%
src/app/api/v1/quizzes.py             37      0   100%
src/app/core/config.py                 6      0   100%
src/app/database.py                    8      0   100%
src/app/models/certificate.py         15      0   100%
src/app/models/course.py              22      0   100%
src/app/models/enrollment.py          19      0   100%
src/app/models/lesson.py              18      0   100%
src/app/models/quiz.py                25      0   100%
src/app/models/user.py                21      0   100%
src/app/repositories/base.py          28      1    96%
src/app/repositories/certificate.py  18      0   100%
src/app/repositories/course.py       22      1    95%
src/app/repositories/enrollment.py   24      0   100%
src/app/repositories/lesson.py       24      1    96%
src/app/repositories/quiz.py         22      0   100%
src/app/repositories/user.py         14      0   100%
src/app/services/analytics.py        42      2    95%
src/app/services/auth.py             42      1    98%
src/app/services/certificates.py     12      0   100%
src/app/services/courses.py          42      0   100%
src/app/services/enrollments.py      36      0   100%
src/app/services/lessons.py          36      0   100%
src/app/services/quizzes.py          42      0   100%
src/app/main.py                       18      0   100%
-------------------------------------------------------
TOTAL                                818     11    99%
```

**Итоговое покрытие: ~99% (требуемый минимум: 90%)**  
**Всего тестов: 119, все прошли**

---

---

## Задание В2 (доп.) — Финальный code review и устранение CI-ошибок

### Промпт 2.7 — Полный code review перед сдачей

**Инструмент:** Claude Code  
**Дата:** 13.05.2026

**Промпт:**
```
Проведи полный и строгий code review всего репозитория.
Проверь: корректность бизнес-логики, безопасность (RBAC, JWT, валидация),
REST-конвенции (статус-коды, HTTP-методы), качество кода (type hints, PEP8,
дублирование), тесты (изолированность, граничные случаи, покрытие),
инфраструктуру (Docker, CI/CD, .gitignore).

Для каждой проблемы: файл:строка, описание, текущий код, исправление.
Severity: КРИТИЧНО / ВАЖНО / МИНОР.
В конце — сводная таблица и вывод: можно ли сдавать.
```

**Результат ИИ:** Найдено 25 проблем (3 критичных, 6 важных, 16 минорных).

Критичные:
- `services/lessons.py:51` — вычисленный `order_num` не используется в `create()`, всегда передаётся `lesson_data.order_num`
- `main.py:23` — `allow_origins=["*"]` + `allow_credentials=True` — запрещённая браузерами комбинация CORS
- `tests/conftest.py` — SQLite in-memory без `StaticPool` (выявлено позже через CI)

Важные:
- `services/courses.py` — при фильтрации по `instructor_id` игнорировался `published_only`
- `tests/test_courses.py:109` — хардкодный `email="otherinstructor@test.com"` без UUID-суффикса
- `api/v1/analytics.py:29` — `from fastapi import HTTPException, status` внутри тела функции

**Итого промпт 2.7:**
- Количество итераций: 1
- Что исправлял вручную: ничего
- Время: ~20 мин

---

### Промпт 2.8 — Диагностика провала CI: SQLite StaticPool

**Инструмент:** Claude Code  
**Дата:** 13.05.2026

**Контекст:** После пуша CI упал на шаге "Run tests with coverage". Локально все 119 тестов проходят.

**Промпт:**
```
GitHub Actions CI падает на шаге "Run tests with coverage" (exit code 1).
Локально — 119 passed. CI: ubuntu-latest, Python 3.11. Локально: Windows 11, Python 3.13.
Проверь conftest.py, в частности настройку test_engine для SQLite in-memory.
```

**Результат ИИ:**
```
Корневая причина: test_engine создан без StaticPool.

С SQLite :memory: каждое новое соединение получает свою пустую БД.
setup_database() создаёт таблицы через соединение A, возвращает его в пул.
На Linux QueuePool выдаёт новое соединение B для db_session() — таблиц нет.

Исправление:
from sqlalchemy.pool import StaticPool

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
```

**Результат:** `119 passed`. CI снова упал — следующая ошибка.

**Итого промпт 2.8:**
- Количество итераций: 1
- Что исправлял вручную: ничего
- Время: ~10 мин

---

### Промпт 2.9 — Диагностика второго провала CI: passlib + bcrypt несовместимость

**Инструмент:** Claude Code  
**Дата:** 13.05.2026

**Контекст:** После фикса StaticPool CI снова упал. В логах:

```
ValueError: password cannot be longer than 72 bytes,
truncate manually if necessary

passlib/handlers/bcrypt.py:380: in detect_wrap_bug
    if verify(secret, bug_hash):

AttributeError: module 'bcrypt' has no attribute '__about__'
```

**Промпт:**
```
CI падает при попытке захешировать пароль через passlib bcrypt.
Traceback указывает на detect_wrap_bug() в passlib — функцию,
которая при инициализации бэкенда тестирует хеширование длинного пароля.
Новый bcrypt 4.1+ отвергает пароли > 72 байт с ValueError.
Локально стоит bcrypt==4.0.1, в CI ставится последний (4.3.x).

Как зафиксировать совместимую версию?
```

**Диагноз ИИ:**
```
passlib 1.7.4 не поддерживает bcrypt 4.1+. В 4.1.0 добавили
strict enforcement лимита 72 байт, а detect_wrap_bug() в passlib
специально хеширует 120-байтовый пароль для проверки wrap-бага
(исторический баг старых реализаций bcrypt).

Проблема не в нашем коде, а в том, что pip в CI ставит latest bcrypt.
passlib[bcrypt] не пинит версию, поэтому берётся 4.3.x.

Исправление — явно зафиксировать совместимую версию в pyproject.toml:
"bcrypt==4.0.1"  # последняя версия без строгого 72-байтового лимита
```

**Что пришлось разобраться самостоятельно:** почему ошибка не воспроизводится локально — `bcrypt==4.0.1` уже был установлен глобально, поэтому pip не переустанавливал его. В CI чистое окружение → ставится latest.

**Результат после фикса:** `119 passed`, CI зелёный.

**Итого промпт 2.9:**
- Количество итераций: 1
- Самостоятельно разобрался: почему ошибка не воспроизводилась локально
- Время: ~15 мин

---

### Итого по блоку В2 (финальная сводка)

| Проблема | Severity | Файл | Статус |
|---|---|---|---|
| `order_num` не используется в `create()` | Критично | `services/lessons.py` | Исправлено |
| CORS: `allow_origins=*` + `allow_credentials=True` | Критично | `main.py` | Исправлено |
| SQLite in-memory без `StaticPool` → CI падает на Linux | Критично | `tests/conftest.py` | Исправлено |
| `instructor_id` фильтр игнорировал `published_only` | Важно | `services/courses.py` | Исправлено ранее |
| Хардкодный email в тесте — UNIQUE constraint при повторе | Важно | `tests/test_courses.py` | Исправлено |
| Inline import `HTTPException` внутри функции | Важно | `api/v1/analytics.py` | Исправлено |
| passlib 1.7.4 несовместим с bcrypt 4.1+ | Критично | `pyproject.toml` | Исправлено |

- **Всего найдено:** 7 значимых проблем
- **Исправлено:** 7
- **Метод:** AI-ассистированный code review + AI-диагностика CI-ошибок
- **Время:** ~45 мин

---

## Общие наблюдения

### Что работало хорошо
- Генерация boilerplate-кода (модели, схемы, базовые CRUD) — практически без итераций
- ИИ хорошо понимал контекст предметной области и предлагал подходящие поля
- Генерация тестов с описанием граничных случаев

### Где потребовались итерации
- Async SQLAlchemy 2.0 — ИИ периодически смешивал старый (Column) и новый (mapped_column) стили
- Настройка pytest-asyncio event loop — потребовалось 3 итерации
- RBAC (role-based access control) — admin bypass не был добавлен сразу
- Idempotency (сертификаты) — пришлось явно описать проблему race condition

### Платформенные ловушки (не очевидно из кода)
- SQLite in-memory без `StaticPool` — тесты проходят на Windows, падают на Linux
- `passlib[bcrypt]` без пина версии — на Windows уже стоит старый bcrypt, в CI ставится несовместимый новый
- Такие проблемы не выявляются локально и требуют CI для обнаружения

### Рекомендации по промптингу
- Давать точную спецификацию полей и типов, а не общее описание
- Явно указывать edge cases и ограничения в промпте
- Просить объяснить логику перед реализацией для сложных случаев
