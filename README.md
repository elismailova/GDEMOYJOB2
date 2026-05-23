# Job Matcher Bot

Telegram-бот для подбора вакансий на основе NLP-анализа резюме с интеграцией HH.ru API.

## Быстрый старт

### 1. Установка зависимостей

```bash
cd "D:\РЭУ магистратура\2 семестр\...\GDEMOYJOB"
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Настройка

Откройте `.env` и вставьте токен бота от [@BotFather](https://t.me/BotFather):

```
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
```

### 3. Запуск

```bash
python -m bot.main
```

При первом запуске автоматически скачивается NLP-модель (~400 МБ). Это занимает несколько минут.

---

## Архитектура

```
GDEMOYJOB/
├── bot/                    # Telegram-бот (aiogram 3)
│   ├── handlers/           # Хендлеры команд и сообщений
│   │   ├── start.py        # /start, /help, профиль
│   │   ├── resume.py       # Загрузка и обработка резюме
│   │   └── search.py       # Поиск вакансий, результаты, skill gap
│   ├── keyboards/
│   │   └── inline.py       # Все клавиатуры (inline + reply)
│   ├── middlewares/
│   │   └── db.py           # Инжекция AsyncSession в хендлеры
│   ├── states.py           # FSM-состояния
│   └── main.py             # Точка входа
├── nlp/                    # NLP-модули
│   ├── parser.py           # Извлечение текста из PDF/DOCX/DOC/TXT
│   ├── analyzer.py         # Парсинг резюме (навыки, опыт, должность)
│   ├── matcher.py          # Семантическое сопоставление + Skill Gap
│   └── skills_vocab.py     # Словарь навыков (IT + soft skills)
├── integrations/
│   └── hh_api.py           # Клиент HH.ru API
├── services/
│   ├── resume_service.py   # Оркестрация: файл → NLP → БД
│   └── search_service.py   # Оркестрация: поиск → ранжирование → история
├── database/
│   ├── models.py           # SQLAlchemy модели (User, Resume, SearchHistory)
│   ├── repository.py       # CRUD-операции
│   └── engine.py           # Async SQLAlchemy engine
└── config.py               # Конфигурация из .env
```

## Функциональность

| Блок | Функция |
|------|---------|
| **Резюме** | PDF, DOCX, DOC, TXT до 10 МБ или текст сообщением |
| **NLP-парсинг** | Навыки, опыт, образование, желаемая должность |
| **Поиск** | HH.ru API: должность, город, зарплата, опыт, занятость |
| **Ранжирование** | Семантика (60%) + совпадение навыков (40%), порог ≥ 0.3 |
| **Результаты** | Топ-10 вакансий с % соответствия и совпадающими навыками |
| **Skill Gap** | Дефицитные навыки ранжированы по частоте в вакансиях |

## Алгоритм ранжирования

```
score = 0.6 × semantic_similarity + 0.4 × skill_overlap_ratio
```

- `semantic_similarity` — косинусное сходство эмбеддингов (модель `paraphrase-multilingual-MiniLM-L12-v2`)
- `skill_overlap_ratio` — доля навыков резюме, найденных в описании вакансии
- Порог отсечения: `score ≥ 0.3`
- Возвращается топ-10 результатов

## Участие в разработке

Правила работы с ветками и формат коммитов описаны в [CONTRIBUTING.md](CONTRIBUTING.md).

## Тестирование

- Автотесты (53 шт.): `pytest -v` — unit + integration тесты NLP и БД
- Отчёт о ручном тестировании: [TEST_REPORT.md](TEST_REPORT.md) — 7 тест-кейсов, 6 PASS / 1 BLOCKED

## Технологии

- **aiogram 3.x** — Telegram Bot API
- **sentence-transformers** — многоязычные эмбеддинги для семантического поиска
- **SQLAlchemy 2.0 async** + **aiosqlite** — асинхронная БД
- **PyMuPDF** — парсинг PDF
- **python-docx** — парсинг DOCX
- **aiohttp** — HTTP-клиент для HH.ru API
