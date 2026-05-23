# JobMatch Bot

[![CI](https://github.com/elismailova/GDEMOYJOB2/actions/workflows/ci.yml/badge.svg)](https://github.com/elismailova/GDEMOYJOB2/actions/workflows/ci.yml)

Telegram-бот для подбора вакансий на основе NLP-анализа резюме с интеграцией API TrudVsem (Роструд).

---

## Быстрый старт

### 1. Клонировать репозиторий и установить зависимости

```bash
git clone https://github.com/elismailova/GDEMOYJOB2.git
cd GDEMOYJOB2
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux / macOS
pip install -r requirements.txt
```

### 2. Настроить переменные окружения

Скопировать `.env.example` → `.env` и вставить токен бота от [@BotFather](https://t.me/BotFather):

```
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
```

### 3. Запустить

```bash
python -m bot.main
```

> При первом запуске автоматически скачивается NLP-модель (~400 МБ) — занимает несколько минут.

---

## Архитектура

```
GDEMOYJOB/
├── bot/                        # Telegram-бот (aiogram 3)
│   ├── handlers/
│   │   ├── start.py            # /start, /help, /cancel, /profile
│   │   ├── resume.py           # Загрузка резюме (файл / текст)
│   │   └── search.py           # Поиск вакансий, результаты, Skill Gap
│   ├── keyboards/
│   │   └── inline.py           # Inline- и reply-клавиатуры
│   ├── middlewares/
│   │   └── db.py               # Инжекция AsyncSession в хендлеры
│   ├── states.py               # FSM-состояния
│   └── main.py                 # Точка входа
├── nlp/                        # NLP-модули
│   ├── parser.py               # Извлечение текста из PDF/DOCX/TXT
│   ├── analyzer.py             # Парсинг резюме (навыки, опыт, должность)
│   ├── matcher.py              # Семантическое сопоставление + Skill Gap
│   └── skills_vocab.py         # Словарь навыков (IT + soft skills)
├── integrations/
│   ├── trudvsem_api.py         # Клиент TrudVsem API (Роструд) — основной
│   ├── hh_api.py               # Клиент HH.ru API
│   └── superjob_api.py         # Клиент SuperJob API
├── services/
│   ├── resume_service.py       # Оркестрация: файл → NLP → БД
│   └── search_service.py       # Оркестрация: поиск → ранжирование → история
├── database/
│   ├── models.py               # SQLAlchemy модели (User, Resume, SearchHistory)
│   ├── repository.py           # CRUD-операции
│   └── engine.py               # Async SQLAlchemy engine
├── tests/                      # Автотесты (53 шт.)
│   ├── conftest.py             # Мок sentence-transformers для CI
│   ├── test_analyzer.py        # Unit-тесты NLP-анализатора
│   ├── test_matcher.py         # Unit-тесты алгоритма матчинга
│   └── test_database.py        # Integration-тесты репозитория БД
├── .github/workflows/
│   └── ci.yml                  # CI/CD: lint (ruff) + тесты (pytest)
├── config.py                   # Конфигурация из .env
├── pytest.ini                  # Настройки pytest
├── ruff.toml                   # Настройки линтера ruff
├── requirements.txt            # Зависимости проекта
├── requirements-dev.txt        # Зависимости для разработки (pytest, ruff)
├── requirements-ci.txt         # Лёгкие зависимости для CI (без ML-моделей)
├── CONTRIBUTING.md             # Git Flow и Conventional Commits
└── TEST_REPORT.md              # Отчёт о ручном тестировании
```

---

## Функциональность

| Блок | Описание |
|------|----------|
| **Резюме** | PDF, DOCX, TXT до 10 МБ или текст сообщением |
| **NLP-парсинг** | Навыки, опыт (лет), уровень, образование, желаемая должность, зарплата |
| **Поиск** | TrudVsem API: должность, город, зарплата, опыт, тип занятости |
| **Ранжирование** | Семантика (60%) + совпадение навыков (40%), порог ≥ 0.1 |
| **Результаты** | Топ-5 вакансий с % соответствия и совпадающими навыками |
| **Skill Gap** | Дефицитные навыки, ранжированные по частоте в топ-вакансиях |
| **История** | Сохранение поисков в БД |

---

## Алгоритм ранжирования

```
score = 0.6 × semantic_similarity + 0.4 × skill_overlap_ratio
```

- `semantic_similarity` — косинусное сходство эмбеддингов (модель `paraphrase-multilingual-MiniLM-L12-v2`)
- `skill_overlap_ratio` — доля навыков резюме, найденных в тексте вакансии
- Порог отсечения: `score ≥ 0.1`
- Возвращается топ-5 результатов

---

## Тестирование

```bash
# Установить зависимости для разработки
pip install -r requirements-dev.txt

# Запустить все тесты
pytest -v

# Запустить линтер
ruff check .
```

- Автотесты (53 шт.): unit + integration для NLP и БД — [tests/](tests/)
- Отчёт о ручном тестировании (7 сценариев): [TEST_REPORT.md](TEST_REPORT.md)
- CI/CD: каждый push автоматически проверяется на GitHub Actions

---

## Участие в разработке

Правила работы с ветками (Git Flow) и формат коммитов (Conventional Commits) описаны в [CONTRIBUTING.md](CONTRIBUTING.md).

---

## Технологии

| Библиотека | Назначение |
|------------|-----------|
| **aiogram 3.13** | Telegram Bot API |
| **sentence-transformers** | Многоязычные эмбеддинги для семантического поиска |
| **SQLAlchemy 2.0 async** + **aiosqlite** | Асинхронная работа с БД |
| **PyMuPDF** | Парсинг PDF |
| **python-docx** | Парсинг DOCX |
| **aiohttp** | HTTP-клиент для API |
| **ruff** | Линтер (статический анализ кода) |
| **pytest** + **pytest-asyncio** | Автотесты |
