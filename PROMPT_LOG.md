# Prompt Log

**Проект:** Платформа онлайн-обучения  
**ФИО:** Евланичев Максим Юрьевич  
**Группа:** 221131  
**ЛР №12, Вариант 7 (повышенная сложность)**

---

## Задание В1: Создание веб-приложения

### Промпт 1

**Инструмент:** Claude Code

"Мне нужна структура Python-проекта для платформы онлайн-обучения. Предметная область: курсы, уроки, студенты, тесты, сертификаты. Используй src-layout, pyproject.toml без setup.py. Какие зависимости нужны для FastAPI + SQLAlchemy 2.0 async + PostgreSQL?"

Результат:  
Получил pyproject.toml с зависимостями и src-layout конфигурацией. ИИ изначально предложил setup.cfg — попросил переделать на современный формат pyproject.toml.

### Промпт 2

**Инструмент:** Claude Code

"Создай SQLAlchemy 2.0 модели с Mapped[] типизацией: User (id, email, username, hashed_password, role: student/instructor/admin, is_active, created_at), Course (id, title, description, instructor_id FK, level enum, price, is_published, tags, created_at). Используй DeclarativeBase, relationship с back_populates."

Результат:  
Модели созданы, но ИИ использовал Column() в нескольких местах вместо mapped_column(). Попросил переписать полностью на новый стиль SQLAlchemy 2.0.

### Промпт 3

**Инструмент:** Claude Code

"Добавь оставшиеся модели: Lesson (course_id FK, order_num, duration_minutes, is_published), Enrollment (student_id FK, course_id FK, UniqueConstraint, progress float), Quiz (course_id FK, questions JSON, passing_score), QuizAttempt, Certificate (enrollment_id unique FK, certificate_number unique)."

Результат:  
Все 5 моделей созданы. Пришлось вручную поправить back_populates в Certificate — ИИ указал неверное имя обратной связи с Enrollment.

### Промпт 4

**Инструмент:** Claude Code

"Создай generic BaseRepository[ModelType] с TypeVar для async CRUD (get, get_multi, create, update, delete, count). Потом специфические репозитории: UserRepository с get_by_email, CourseRepository с get_by_instructor и get_published, EnrollmentRepository с update_progress (автоматически ставит completed_at при progress=100), CertificateRepository."

Результат:  
Репозиторий создан. Проблема: get_multi() принимал **filters, но не применял их к SQL-запросу — передавались как kwargs но условие WHERE не добавлялось. Исправил через следующий промпт.

### Промпт 5

**Инструмент:** Claude Code

"В BaseRepository.get_multi() filters не применяются к запросу. Сделай: for key, value in filters.items(): stmt = stmt.where(getattr(self.model, key) == value). Добавь проверку hasattr на случай несуществующего поля."

Результат:  
Работает. Фильтрация через keyword аргументы теперь корректно добавляет WHERE условия.

### Промпт 6

**Инструмент:** Claude Code

"Создай сервисы: auth.py (register с проверкой уникальности email/username, login с JWT, get_current_user, require_roles — dependency factory), courses.py (create_course, get_course, update_course с проверкой владения, delete_course, publish/unpublish)."

Результат:  
Сервисы написаны. Проблема: require_roles не пропускал admin автоматически — если admin обращался к эндпоинту с require_roles('instructor'), получал 403. Добавил проверку if current_user.role == UserRole.admin: return current_user перед основной логикой.

### Промпт 7

**Инструмент:** Claude Code

"Создай сервисы lessons.py, enrollments.py (запись с проверкой на дубликат, обновление прогресса с автовыдачей сертификата при 100%), quizzes.py (подсчёт score по answers и correct_answer в JSON), certificates.py (идемпотентная выдача), analytics.py (top_courses через func.count, platform_overview для admin)."

Результат:  
ИИ в analytics.py использовал session.execute(text("SELECT...")) вместо SQLAlchemy ORM. Попросил переписать через select() и func.count() — переписал без проблем.

### Промпт 8

**Инструмент:** Claude Code

"Создай FastAPI роутеры для всех сущностей с Annotated + Depends. auth.py: POST /register (201), POST /login (OAuth2PasswordRequestForm), GET /me. courses.py: GET / публичный, POST / для instructor, PUT и DELETE с проверкой владения, POST /{id}/publish. Подключи всё в main.py с CORS middleware и GET /health."

Результат:  
Роутеры созданы. GET /courses/ требовал авторизацию — исправил через отдельный промпт, убрал Depends. POST /register возвращал 200 вместо 201 — поправил status_code.

### Промпт 9

**Инструмент:** Claude Code

"Создай Alembic конфигурацию для async SQLAlchemy: alembic.ini, env.py с asyncio.run() и импортом всех моделей, версию миграции 001_initial_schema.py создающую все 7 таблиц с FK, UniqueConstraint, индексами."

Результат:  
Миграция создана. Работает корректно.

### Промпт 10

**Инструмент:** Claude Code

"Создай Dockerfile (python:3.11-slim, WORKDIR /app, PYTHONPATH=/app/src, CMD запускает alembic upgrade head и uvicorn) и docker-compose.yml (postgres:16-alpine с healthcheck pg_isready, app depends_on с condition: service_healthy, volumes для данных)."

Результат:  
Docker конфигурация создана. В CMD не было && между командами — пришлось переделать на shell форму: CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app ..."].

### Итого

- Количество промптов: 10
- Что пришлось исправлять вручную: back_populates в модели Certificate
- Время: ~3 часа

---

## Задание В2: Code Review сгенерированного кода

### Промпт 1

**Инструмент:** Claude Code

"Проведи критический code review: repositories/base.py, services/enrollments.py, api/v1/courses.py, api/v1/quizzes.py, schemas/course.py. Найди логические ошибки, уязвимости безопасности, нарушения REST-конвенций, проблемы валидации. Для каждой проблемы — файл:строка, описание, исправление, severity."

Результат:  
Найдено 6 проблем. Критичные: POST-эндпоинты возвращали 200 вместо 201, price не имел ограничения ge=0 (принимал отрицательные значения), race condition при выдаче сертификата (исправлен добавлением проверки существующего сертификата перед созданием). Важные: студент видел неопубликованные уроки (list_lessons не разделял по роли), инструктор мог изменить чужой курс (не было проверки instructor_id == current_user.id). PYTHONPATH отсутствовал в Dockerfile при src-layout. Всё исправлено.

### Промпт 2

**Инструмент:** Claude Code

"Проверь тесты на изолированность. В test_courses.py тест test_update_course_other_instructor_forbidden использует email='otherinstructor@test.com' без UUID-суффикса — при повторном запуске тестов будет UNIQUE constraint violation."

Результат:  
Подтверждено. Исправил хардкодный email добавлением uid = _unique_suffix() и f"otherinstructor_{uid}@test.com".

### Промпт 3

**Инструмент:** Claude Code

"После пуша CI упал: ubuntu-latest, Python 3.11. Локально 119 тестов проходят (Windows 11, Python 3.13). Проверь conftest.py — настройку test_engine для SQLite in-memory."

Результат:  
Корневая причина: без StaticPool на Linux QueuePool открывает новое соединение для каждой сессии, и каждое соединение получает пустую БД (без таблиц). Исправление: добавить poolclass=StaticPool и connect_args={"check_same_thread": False} в create_async_engine. После фикса тесты прошли, но CI упал снова с другой ошибкой.

### Промпт 4

**Инструмент:** Claude Code

"CI падает с: ValueError: password cannot be longer than 72 bytes и AttributeError: module 'bcrypt' has no attribute '__about__'. Traceback указывает на passlib detect_wrap_bug(). Локально стоит bcrypt==4.0.1, в CI ставится последний через pip."

Результат:  
passlib 1.7.4 несовместим с bcrypt 4.1+: в 4.1.0 добавили strict enforcement 72-байтового лимита, а detect_wrap_bug() специально хеширует 120-байтовый пароль. Исправление: явно зафиксировать "bcrypt==4.0.1" в pyproject.toml. После этого CI стал зелёным.

### Итого

- Количество промптов: 4
- Что пришлось исправлять вручную: ничего, все исправления применял ИИ
- Время: ~1.5 часа

---

## Задание В4: CI/CD с интеграцией ИИ

### Промпт 1

**Инструмент:** Claude Code

"Создай GitHub Actions workflow: триггер push и pull_request на main/master/develop, Python 3.11, кэш pip по хешу pyproject.toml, установка pip install -e '.[dev]', запуск pytest --cov=src --cov-report=xml --cov-fail-under=90, загрузка HTML отчёта как артефакт."

Результат:  
Файл .github/workflows/ci.yml создан. Работает с первого раза, порог 90% задан корректно.

### Промпт 2

**Инструмент:** Claude Code

"Создай второй workflow для автоматического AI code review в pull request: получить git diff изменённых .py файлов, отправить в Anthropic API (claude-3-5-sonnet-20241022) с промптом code reviewer, опубликовать ответ как комментарий к PR через GitHub API. Использовать secrets ANTHROPIC_API_KEY и встроенный GITHUB_TOKEN."

Результат:  
Workflow создан. ИИ изначально написал неверный model ID ('anthropic.claude-3-5-sonnet-20241022') — исправил убрав префикс. Workflow корректно отправляет diff в API и постит комментарий к PR.

### Итого

- Количество промптов: 2
- Что пришлось исправлять вручную: ничего
- Время: ~30 мин

---

## Задание В7: Генерация unit-тестов (≥90% покрытие)

### Промпт 1

**Инструмент:** Claude Code

"Создай conftest.py: SQLite in-memory через aiosqlite, create_all() для схемы, override dependency get_session через app.dependency_overrides, фикстуры db_session и test_client через AsyncClient с ASGITransport, фикстуры test_student/test_instructor/test_admin с UUID-суффиксами для изолированности."

Результат:  
conftest.py создан. Проблема: scope='session' для db_session конфликтовал с scope='function' для client — возникала ошибка 'Task attached to a different loop'. Исправил: asyncio_mode='auto' в pyproject.toml, все фикстуры кроме setup_database стали scope='function'.

### Промпт 2

**Инструмент:** Claude Code

"Напиши тесты для auth: POST /register (201, проверить поля ответа), POST /login (200, access_token присутствует), GET /me с токеном (200), дублирование email/username (400), неверный пароль (401), GET /me без токена (401), короткий пароль (422)."

Результат:  
9 тест-кейсов, все проходят.

### Промпт 3

**Инструмент:** Claude Code

"Напиши тесты для courses и lessons: создание курса инструктором (201), студентом (403), получение списка (200 публично), обновление своего (200) и чужого (403), удаление (204), публикация (is_published=True). Для lessons: добавление урока инструктором (201), студент видит только published, инструктор видит все, студент не может добавлять (403)."

Результат:  
15 тест-кейсов. Все прошли.

### Промпт 4

**Инструмент:** Claude Code

"Напиши e2e тесты для enrollment→quiz→certificate: запись на опубликованный курс (201), дублирование (400), обновление прогресса до 100% → автовыдача сертификата, повторный прогресс=100 не создаёт второй сертификат (идемпотентность). Тесты квизов: правильные ответы → passed=True, неправильные → passed=False. Аналитика: top-courses (200), overview для admin (200) и student (403)."

Результат:  
19 тест-кейсов. Покрытие итого: 99% (119 тестов, требуемый минимум 90%).

### Итого

- Количество промптов: 4
- Что пришлось исправлять вручную: ничего
- Время: ~1.5 часа

---

## Задание В2 (доп): Повторный code review и исправление найденных проблем

### Промпт 1

**Инструмент:** Claude Code

"Проверь весь репозиторий ещё раз перед финальной сдачей: посмотри на repositories/base.py, api/v1/courses.py и сервисы. Найди логические ошибки, проблемы авторизации, dead code."

Результат:
Найдено 2 проблемы. Первая: в `BaseRepository.update()` условие `if value is not None or key in kwargs:` всегда `True`, так как `key in kwargs` истинно при итерации по `kwargs.items()` — в результате `None`-значения тоже записывались в БД. Вторая: `GET /courses/{id}/students` не проверял права — любой авторизованный пользователь мог посмотреть список студентов чужого курса. Исправил оба.

### Промпт 2

**Инструмент:** Claude Code

"Исправь BaseRepository.update() — убери мёртвое условие. Добавь проверку авторизации в get_course_students: только инструктор курса или admin."

Результат: Оба исправления применены, тесты прошли.

### Итого

- Количество промптов: 2
- Что пришлось исправлять вручную: ничего
- Время: ~20 мин
