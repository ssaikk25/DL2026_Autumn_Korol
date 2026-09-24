# Погода с настроением

Fullstack-приложение, которое показывает текущую погоду и подбирает под неё релевантный мем.
Рекомендатель обучается на оценках пользователей (Thompson sampling) и со временем показывает
более смешные мемы для каждой погодной категории.

## Возможности

- Поиск города с автодополнением и определение локации по геолокации браузера.
- Текущая погода: температура, «ощущается как», влажность, ветер, облачность, описание.
- Мем под погоду с онлайн-обучением на оценках.
- Кнопка «Другой мем» (повторная выборка рекомендателем).
- Прогноз на 5 дней.
- Шаринг «открытки»: скачивание PNG и Web Share API.
- Авто-категоризация пользовательских мемов (zero-shot по эмбеддингам).
- Демо-режим при недоступности погодного API.

## Стек

| Слой | Технологии |
| ---- | ---------- |
| Frontend | React 18, TypeScript, Vite, Tailwind CSS |
| Backend | Python 3.11+, FastAPI, Uvicorn, Pydantic v2 |
| База данных | SQLite, SQLAlchemy 2.0 |
| ML | fastembed (ONNX-эмбеддинги), NumPy (Thompson sampling), Jupyter |
| Внешние API | Open-Meteo (геокодинг и погода), датасет `foldl/rumeme-desc` |

## Структура

```
.
├── backend/              # FastAPI + ML
│   ├── app/
│   │   ├── routers/          # weather, geocode, memes
│   │   ├── services/         # weather_service, recommender
│   │   └── ml/               # fetch_memes, embedding, categorize, pipeline
│   ├── requirements.txt      # API-зависимости
│   ├── requirements-ml.txt   # ML-пайплайн
│   └── .env.example
├── frontend/             # React + TypeScript + Vite
├── notebooks/            # исследование данных и эксперименты
└── docs/                 # design.md, AI_REFLECTION.md
```

## Требования

- Python 3.11+ (разработка и проверка велись на Python 3.14).
- Node.js 18+ и npm.

## Установка и запуск бэкенда

```bash
cd backend
python -m venv .venv

# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# 1. зависимости API
pip install -r requirements.txt

# 2. (необязательно) зависимости ML-пайплайна — нужны только для шага 4
pip install -r requirements-ml.txt

# 3. (опционально) конфигурация
cp .env.example .env

# 4. (необязательно, но рекомендуется) наполнить базу полным набором мемов
#    из датасета; первый запуск требует интернет — качает датасет и модель
python -m app.ml.pipeline

# 5. запуск сервера
uvicorn app.main:app --reload --port 8000
```

Сервер стартует на `http://127.0.0.1:8000`, интерактивная документация API — `/docs`.

При первом запуске на пустой базе приложение автоматически добавляет стартовый набор
мемов (10 картинок из репозитория), поэтому погода и мемы видны сразу — даже без шагов
2 и 4. `python -m app.ml.pipeline` заменяет стартовый набор полной выборкой из
датасета. Если пайплайн не запускать, база всё равно не останется пустой — приложение
будет показывать стартовые мемы.

## Запуск фронтенда

```bash
cd frontend
npm install
npm run dev
```

Открой `http://localhost:5173`. Dev-сервер проксирует `/api` и `/static` на бэкенд (порт 8000).

## ML-пайплайн

- `python -m app.ml.pipeline` — отбор погодных мемов из датасета (keyword + исключения) и запись в БД;
  при запуске существующие записи (включая стартовый набор) заменяются выборкой из датасета.
- `notebooks/01_meme_pipeline.ipynb` — исследование данных, эмбеддинги, категоризация.
- Рекомендатель (Thompson sampling) обучается онлайн на оценках пользователей, без отдельного этапа
  тренировки; параметры хранятся в таблице `meme_stats`.

## API (кратко)

| Метод | Путь | Описание |
| ----- | ---- | -------- |
| GET | `/api/geocode?q=` | поиск города |
| GET | `/api/weather/current?city=` или `?lat=&lon=` | погода + мем |
| GET | `/api/weather/forecast?city=` | прогноз на 5 дней |
| GET | `/api/memes?category=` | список мемов |
| POST | `/api/memes` | добавить мем (multipart) |
| POST | `/api/memes/{id}/feedback` | оценка |

Полное описание — в [docs/design.md](docs/design.md).

## Тесты

```bash
cd backend
# выполняется в уже активированном виртуальном окружении (см. раздел установки)
pip install -r requirements-dev.txt
python -m pytest tests
```

## Источники данных

- Погода и геокодинг: [Open-Meteo](https://open-meteo.com/) (бесплатно, без ключа).
- Мемы: датасет [foldl/rumeme-desc](https://huggingface.co/datasets/foldl/rumeme-desc)
  (лицензия CC BY-SA 4.0, используется с атрибуцией).

## Документация

- [Проектирование (design.md)](docs/design.md)
- [Рефлексия по использованию AI (AI_REFLECTION.md)](docs/AI_REFLECTION.md)
