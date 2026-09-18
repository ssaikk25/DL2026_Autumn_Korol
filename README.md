# Погода с настроением

Fullstack-приложение, которое показывает текущую погоду и подбирает под неё релевантный мем.
Рекомендатель обучается на оценках пользователей (Thompson sampling) и со временем показывает
более смешные мемы для каждой погодной категории.

## Возможности

- Поиск города с автодополнением и определение локации по геолокации браузера.
- Текущая погода: температура, «ощущается как», влажность, ветер, облачность, описание.
- Мем под погоду с онлайн-обучением на оценках 👍/👎.
- Кнопка «Другой мем» (повторная выборка рекомендателем).
- Прогноз на 5 дней с мемом на каждый день.
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

- Python 3.11+ (рекомендуется 3.11 для совместимости с ML-библиотеками).
- Node.js 18+ и npm.

## Запуск бэкенда

```bash
cd backend
python -m venv .venv

# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt

# опционально, для ML-пайплайна (отбор и категоризация мемов):
pip install -r requirements-ml.txt

# опционально, конфигурация
cp .env.example .env

# опционально, наполнить базу мемами (скачает датасет и модель fastembed)
python -m app.ml.pipeline

uvicorn app.main:app --reload --port 8000
```

Сервер стартует на `http://127.0.0.1:8000`, интерактивная документация API — `/docs`.

## Запуск фронтенда

```bash
cd frontend
npm install
npm run dev
```

Открой `http://localhost:5173`. Dev-сервер проксирует `/api` и `/static` на бэкенд (порт 8000).

## ML-пайплайн

- `python -m app.ml.pipeline` — отбор погодных мемов из датасета (keyword + исключения) и запись в БД.
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
| POST | `/api/memes/{id}/feedback` | оценка 👍/👎 |

Полное описание — в [docs/design.md](docs/design.md).

## Тесты

```bash
cd backend
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
