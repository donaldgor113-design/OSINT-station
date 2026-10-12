# OSINT Workspace

Універсальна веб-платформа для OSINT-фахівців, аналітиків розслідувань та
корпоративної розвідки: єдине робоче місце з підключенням зовнішніх
інструментів, геоінтелектом, AI-аналізом та уніфікованою обробкою даних.

Цей репозиторій — **Фаза 1–2** дорожньої карти (технічний PoC).

## Статус

- [x] Монорепозиторій: `backend/` (FastAPI) + `frontend/` (React + TS + Vite)
- [x] PostgreSQL через Docker Compose
- [x] Схема `UniversalEntity` (SQLAlchemy-модель + Pydantic-схеми)
- [x] Базовий `Adapter` інтерфейс (`search()`, `normalize_response()`)
- [x] `ShodanAdapter` — перша інтеграція
- [x] `GoogleMapsGeocodeAdapter` — геокодування у `location`-сутності
- [x] `WhoisAdapter` (RDAP) — `domain`-сутності
- [x] `TelegramAdapter` — `channel`/`person`-сутності
- [x] AI-модуль: `AIProviderAdapter` + `MockAIProvider` + `ClaudeProvider`
- [x] Робоча область з вкладками (Пошук / Гео / Сутності / Аналіз)
- [x] Геоінт: синхронізовані мульти-мапи (MapLibre + Zustand), Mapillary 360°, таймлайн
- [x] Базові тести адаптерів, нормалізації та AI

## Структура

```
osint-workspace/
├─ docker-compose.yml        # PostgreSQL
├─ backend/
│  ├─ app/
│  │  ├─ main.py             # FastAPI app + CORS + health
│  │  ├─ config.py           # pydantic-settings
│  │  ├─ database.py         # SQLAlchemy engine/session
│  │  ├─ models/             # UniversalEntity (ORM)
│  │  ├─ schemas/            # Pydantic-схеми
│  │  ├─ adapters/           # Adapter interface + Shodan + GoogleMaps + factory
│  │  ├─ ai/                 # AIProviderAdapter + mock + Claude
│  │  ├─ core/               # normalization (entity_id hash, merge)
│  │  ├─ api/routes/         # /api/search, /api/entities, /api/analyze
│  │  └─ services.py         # upsert + серіалізація
│  └─ tests/                 # pytest
└─ frontend/
   └─ src/                   # React: Workspace, SearchBar, EntityCard, Tabs, AnalyzePanel
```

## Запуск

### 1. PostgreSQL

```bash
docker compose up -d
```

### 2. Backend

```bash
cd backend
python -m venv .venv
# Windows:  .venv\Scripts\activate   |  Unix: source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env               # налаштуйте DATABASE_URL / SHODAN_API_KEY
uvicorn app.main:app --reload
```

API доступний на http://localhost:8000 (документація — http://localhost:8000/docs).

Без API-ключа Shodan бекенд у mock-режимі (`SHODAN_MOCK=true`) повертає
зразкові дані, щоб UI працював одразу. Щоб використовувати реальний Shodan,
заповніть `SHODAN_API_KEY` у `.env` та виставте `SHODAN_MOCK=false`.

Для швидкого локального запуску **без Docker** можна увімкнути SQLite:
`DATABASE_URL=sqlite:///./osint.db` у `.env`.

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend на http://localhost:5173 (проксі `/api` → `localhost:8000`).

## Тести

```bash
cd backend
pytest
```

## Ендпоінти

| Метод | Шлях                  | Опис                          |
|-------|-----------------------|-------------------------------|
| POST  | `/api/search`         | Пошук через адаптер джерела   |
| GET   | `/api/entities`       | Усі збережені сутності        |
| GET   | `/api/entities/{id}`  | Сутність за `entity_id`       |
| POST  | `/api/analyze`        | AI-зведення + кросс-перевірка |
| GET   | `/health`             | Статус                        |

`/api/search` приймає `{"query", "source"}` де `source` ∈ `shodan | google_maps | whois | telegram`.

Без API-ключів усі джерела та AI працюють у **mock-режимі** (прапорці
`*_MOCK` у налаштуваннях). Щоб увімкнути реальні сервіси, впиши ключі в
`.env` та вистав відповідний `*_MOCK=false`.

## Дизайнерські рішення

- **Уніфікація:** будь-яке джерело нормалізується в `UniversalEntity`;
  `raw_data` зберігає оригінальну відповідь без змін (аудит + повторна обробка).
- **Злиття:** однакові об'єкти з різних джерел зливаються за `entity_id`
  (SHA-256 від нормалізованих ключових полів), а не дублюються.
- **JSON на SQLite / JSONB на PostgreSQL** — тести працюють без Docker.
