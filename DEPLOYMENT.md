# Deployment Guide — JobMatch Bot

## Содержание

1. [Требования](#требования)
2. [Локальный запуск](#локальный-запуск)
3. [Деплой на Railway](#деплой-на-railway)
4. [Переменные окружения](#переменные-окружения)

---

## Требования

| Инструмент | Версия |
|-----------|--------|
| Python | 3.10+ |
| Git | любая |
| Telegram Bot Token | от [@BotFather](https://t.me/BotFather) |
| (для Railway) Аккаунт | [railway.app](https://railway.app) |

---

## Локальный запуск

### 1. Клонировать репозиторий

```bash
git clone https://github.com/elismailova/GDEMOYJOB2.git
cd GDEMOYJOB2
```

### 2. Создать виртуальное окружение

```bash
python -m venv venv
```

### 3. Установить зависимости

```bash
# Windows
.\venv\Scripts\pip.exe install -r requirements.txt

# Linux / macOS
venv/bin/pip install -r requirements.txt
```

### 4. Настроить переменные окружения

Скопировать `.env.example` → `.env`:

```bash
copy .env.example .env   # Windows
cp .env.example .env     # Linux / macOS
```

Открыть `.env` и заполнить:

```env
BOT_TOKEN=ваш_токен_от_BotFather
DATABASE_URL=sqlite+aiosqlite:///./job_matcher.db
```

### 5. Запустить бота

```bash
# Windows
.\venv\Scripts\python.exe -m bot.main

# Linux / macOS
venv/bin/python -m bot.main
```

> При первом запуске автоматически скачивается NLP-модель (~400 МБ). Это занимает 2–5 минут.  
> При повторных запусках модель загружается из кэша — старт занимает несколько секунд.

### 6. Запустить тесты и линтер

```bash
.\venv\Scripts\pip.exe install -r requirements-dev.txt

.\venv\Scripts\python.exe -m pytest -v      # тесты
.\venv\Scripts\python.exe -m ruff check .   # линтер
```

---

## Деплой на Railway

Railway — облачная платформа, которая автоматически деплоит бота при каждом `git push`.

### Шаг 1 — Зарегистрироваться

Перейти на [railway.app](https://railway.app) → **Login with GitHub**.

### Шаг 2 — Создать проект

**New Project → Deploy from GitHub repo → elismailova/GDEMOYJOB2**

Railway обнаружит `Dockerfile` и начнёт сборку автоматически.

### Шаг 3 — Добавить PostgreSQL

В проекте: **+ New → Database → Add PostgreSQL**

Railway создаст базу данных и автоматически добавит переменную `DATABASE_URL` в окружение сервиса.

### Шаг 4 — Добавить переменные окружения

Перейти в сервис **GDEMOYJOB2** → вкладка **Variables** → **New Variable**:

| Переменная | Значение |
|-----------|---------|
| `BOT_TOKEN` | токен от @BotFather |

> `DATABASE_URL` добавляется автоматически при подключении PostgreSQL.

### Шаг 5 — Проверить деплой

Вкладка **Deployments** → последний деплой → **View Logs**.

Ожидаемые строки в логах:
```
Инициализация БД...
Загрузка NLP-модели...
Бот запущен.
Запуск polling...
```

> Первая сборка занимает **10–15 минут** — в образ встраивается PyTorch и NLP-модель (~900 МБ).  
> Последующие деплои быстрее — Railway кэширует слои Docker-образа.

### Автодеплой

После первоначальной настройки Railway следит за репозиторием. Каждый `git push origin master` автоматически запускает новый деплой без дополнительных действий.

---

## Переменные окружения

| Переменная | Обязательная | Описание | Пример |
|-----------|:---:|---------|--------|
| `BOT_TOKEN` | ✅ | Токен Telegram-бота от @BotFather | `1234567890:ABC...` |
| `DATABASE_URL` | ✅ | URL базы данных | `sqlite+aiosqlite:///./job_matcher.db` или `postgresql://...` |

### Форматы DATABASE_URL

**SQLite** (локальная разработка):
```
sqlite+aiosqlite:///./job_matcher.db
```

**PostgreSQL** (Railway — подставляется автоматически):
```
postgresql://user:password@host:5432/dbname
```

> Приложение автоматически преобразует `postgresql://` → `postgresql+asyncpg://` для работы с async SQLAlchemy.

---

## Структура Docker-образа

```dockerfile
FROM python:3.10-slim
# CPU-версия PyTorch (~500 МБ вместо ~2 ГБ)
# Все зависимости из requirements.txt
# Предзагруженная NLP-модель paraphrase-multilingual-MiniLM-L12-v2
CMD ["python", "-m", "bot.main"]
```

Образ содержит предзагруженную NLP-модель, поэтому бот стартует мгновенно без ожидания скачивания.
