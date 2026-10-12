# Хід розробки — OSINT Workspace (фактичний стан)

> Цей документ описує, що **реально реалізовано** в коді на цей момент.
> Призначений для звірки з ТЗ (`OSINT Workspace — Технічна специфікація проєкту.pdf`)
> та для продовження роботи після перерви.

Дата останнього оновлення: 2026-10-11

---

## 1. Загальний стек

| Шар | Технологія |
|-----|-----------|
| Frontend | React 18 + TypeScript + Vite, Zustand, MapLibre GL JS |
| Backend | Python, FastAPI (async), SQLAlchemy 2, Pydantic v2 |
| БД | SQLite (розробка) / PostgreSQL 16 (через Docker Compose) |
| Зовнішні виклики | httpx |
| Зображення | Pillow (EXIF), python-multipart (upload) |
| Браузерна автоматизація | Playwright (Chromium) |
| AI | Ollama (локально), Anthropic Claude, OpenAI/OpenAI-сумісні API |
| Гео/мапи | MapLibre GL JS (OSM + CARTO), Mapillary (360°), Nominatim (геокодинг) |

---

## 2. Backend

### 2.1 Моделі (`app/models/`)
- `Workspace` — дослідження/розслідування, ізоляція даних.
- `UniversalEntity` — уніфікована сутність (spec §4). Прив'язана до `workspace_id`;
  унікальність `(workspace_id, entity_id)`. Поля: `entity_type`, `entity_id`,
  `entity_name`, `properties` (JSON: geo/temporal/digital_footprint/metadata/domain/company/document),
  `relations`, `raw_data`.
- `ProviderConfig` — користувацькі AI-провайдери.

### 2.2 Адаптери джерел (`app/adapters/`)
Спільний інтерфейс `Adapter` (`search()`, `normalize_response()`).

| Адаптер | source | entity_type | Статус |
|---------|--------|-------------|--------|
| `ShodanAdapter` | `shodan` | `ip` | **mock** (потрібен платний ключ) |
| `GoogleMapsGeocodeAdapter` | `google_maps` | `location` | **mock** (потрібен ключ) |
| `WhoisAdapter` (RDAP) | `whois` | `domain` | **реальний** (без ключа), фолбек mock |
| `TelegramAdapter` | `telegram` | `channel`/`person` | **mock** |
| `CompanyScraperAdapter` | `company_scraper` | `company` | статичний скрапінг (httpx, `<title>`) |
| `WebSearchAdapter` | `web_search` | `document` | **реальний** веб-пошук |
| `SocialBrowserAdapter` | `social_browser` | `document` | Playwright-рендер сторінки |
| `CompanyProfileAdapter` | `company_profile` | `company` | **агрегований профіль компанії** (основний) |
| `RegistrySearchAdapter` | `registry` | `company` | **пошук у локальній БД ЄДР** (data.gov.ua) — перший у черзі пошуку |
| `CompanyRegistryAdapter` | `company_registry` | `company` | mock (застарілий, не в auto-flow) |

### 2.3 Розумний пошук (`app/api/routes/search.py`)
Один пошуковий рядок з **автовизначенням типу запиту**:
- IPv4 → `shodan`
- 8 цифр (ЄДРПОУ) / 10 цифр (ІПН) → `company_profile`
- домен (`example.com`) → `whois`
- решта (назва, прізвище, адреса) → `company_profile`

### 2.4 Профіль компанії (`CompanyProfileAdapter`)
Алгоритм для назви компанії:
1. Веб-пошук (топ-30 результатів).
2. Класифікація: Вікіпедія / соцмережі / реєстр / офіційний сайт / згадка.
3. **Витяг юридичних даних з тайтлів і сніпетів** (ЄДРПОУ, назва «ТОВ …», адреса, керівник, статус, КВЕД, капітал, телефон, email, контактна особа).
4. **Відкриття топ-5 сторінок** (спершу агрегатори реєстрів) і парсинг з HTML.
5. **Зображення** — Bing image search, перші 5 URL.
6. Злиття всього в одну картку.

Для ЄДРПОУ:
1. **Прямий запит у реєстри** за кодом: `clarity-project.info`, `opendatabot.ua`, `ring.org.ua`, `youcontrol.com.ua`.
2. Фолбек — веб-пошук `"ЄДРПОУ <код>"` + витяг зі сніпетів.
3. **OpenDataBot API** — заглушка (`OPENDATABOT_API_KEY`, платний).
4. Додається посилання `https://opendatabot.ua/c/<код>`.

### 2.5 Веб-пошук (`app/adapters/web_search.py`)
Багаторівневий пошук (для надійності, без платних API):
1. Google Custom Search (якщо ключ) / Brave (якщо ключ) — **платні, опційно**.
2. HTTP-пошуковики в порядку: **Bing → DuckDuckGo → DDG Lite**.
3. **Playwright** (реальний Chromium) — останній рубіж.
+ Кеш результатів, пауза 2.5 с між запитами (щоб не перевищувати rate limit).
+ Розкодування Bing-redirect посилань (`u=a1<base64>`) і DDG-redirect (`uddg=`).

### 2.6 AI-модуль (`app/ai/`)
- `AIProviderAdapter` — інтерфейс (`summarize`, `cross_check`).
- Провайдери: `MockAIProvider` (детермінований), `OllamaProvider` (локально),
  `ClaudeProvider`, `OpenAIProvider` (OpenAI **або будь-який OpenAI-сумісний** API).
- `providers.available(db)` / `providers.get(name, db)` — вбудовані + користувацькі.
- `detect_anomalies()` — евристика (застарілі дані, гео-викиди).
- `vision.py` — `describe_image`, `verify_location` (звірка GPS↔вміст, Ollama vision).

### 2.7 Медіа/зображення (`app/media/`)
- `exif.py` — EXIF/GPS/дата/пристрій/роздільність (Pillow, реальний).
- `geocode.py` — `forward_geocode` (адреса→координати) і `reverse_geocode` (координати→адреса), Nominatim, реальний.
- `heuristics.py` — не-AI перевірки метаданих (GPS=0,0, дата в майбутньому).

### 2.8 Локальна БД реєстрів (ЄДР з data.gov.ua)
- Моделі `LegalEntity` (юридичні особи, ЄДРПОУ) та `IndividualEntrepreneur` (ФОП, РНОКПП) у `app/models/registry.py`.
- Імпортер `app/registry/importer.py` (мапінг полів data.gov.ua → схема) + CLI `scripts/import_registry.py`.
- `RegistrySearchAdapter` (`app/adapters/registry_search.py`) — пошук за ЄДРПОУ/ІПН/назвою в локальній БД.
- Маршрут `/api/search` **спершу шукає в локальній БД**, і лише якщо порожньо — падає на веб-пошук.
- Для великого обсягу даних рекомендується **PostgreSQL** (не SQLite).

### 2.9 Ендпоінти (`app/api/routes/`)

| Метод | Шлях | Опис |
|-------|------|------|
| GET/POST | `/api/workspaces` | список / створення дослідження |
| GET/DELETE | `/api/workspaces/{id}` | отримати / видалити |
| POST | `/api/search` | розумний пошук (`{query, source="auto", workspace_id}`) |
| GET | `/api/entities?workspace_id=` | сутності дослідження |
| POST | `/api/analyze` | аналіз (`{workspace_id, entity_ids, provider}`) |
| POST | `/api/geocode` | геокодинг (Nominatim, без збереження) |
| POST | `/api/images/analyze` | аналіз зображення (multipart) |
| GET/POST | `/api/ai/providers` | AI-моделі + додавання кастомної |
| DELETE | `/api/ai/providers/{id}` | видалення кастомної моделі |
| GET | `/health` | статус |

---

## 3. Frontend

### 3.1 Каркас
- `Sidebar` — ліве меню (SVG-іконки): Пошук, Гео-мапи, Зображення, Сутності, Аналіз (вгорі); Налаштування, Профіль (внизу).
- `TopBar` — назва розділу + вибір дослідження + «+ Нове» + профіль.
- `Workspace.tsx` — коренева компоновка.

### 3.2 Сторінки
- **Пошук** — один рядок, автовизначення типу. Результат: для компанії — **широка картка на весь екран**, для списку (веб-пошук) — сітка карток.
- **Картка компанії** (`EntityCard`) — блоки:
  - Вікіпедія (якщо є)
  - **Юридична інформація** — сітка 2 колонки: ЄДРПОУ, форма, адреса, директор, контактна особа, телефон, email, засновники, дата, статус, КВЕД, капітал, податковий статус, контакти. Порожнє поле → **червоний курсив «інформація не знайдена»**.
  - **Міні-карта** з маркером (якщо є адреса → координати).
  - **Посилання** — Сайт і OpenDataBot (окремо, «інформація не знайдена» якщо немає).
  - **Соцмережі**, **Згадки**, **Зображення** (внизу блоку, перші 5, в один ряд однаковим розміром, клік → лайтбокс по центру з кнопкою закриття).
- **Гео-мапи** — синхронізовані мульти-мапи (велика + 3 малі, змінні місцями), таймлайн, метадані. Провайдери: OSM, CARTO dark, супутник (mock), Mapillary 360°.
  - **Блок «Адреси в розслідуванні»** — лише сутності з реальною адресою; клік центрує всі мапи + ставить червоний маркер.
  - **Пошук** (адреса/координати) — реальний геокодинг (Nominatim) + маркер.
- **Зображення** — EXIF/GPS, адреса, перевірки (без AI + візуальна), «показати на карті».
- **Сутності** — список поточного дослідження.
- **Аналіз** — вибір сутностей + вибір AI-моделі → зведення/кросс-перевірка/аномалії.
- **Налаштування** — керування AI-моделями (додати/видалити кастомну).
- **Профіль** — заглушка.

### 3.3 Стейт (`store/`)
- `mapState.ts` — центр/зум/таймлайн + **фокус-точка (маркер)**.
- `workspaceState.ts` — поточне дослідження.

### 3.4 Легасі (не використовується)
- `Tabs.tsx`, `WorkspaceBar.tsx`, `SettingsModal.tsx`.

---

## 4. Мапа на специфікацію (roadmap)

| Фаза | Назва | Статус |
|------|-------|--------|
| 1 | Фундамент | ✅ виконано |
| 2 | Ядро аналізу | ✅ виконано |
| 3 | Геоінтелект (мульти-мапи, 360°, таймлайн) | ✅ виконано |
| 4 | Соцмережі та компанії | ⚠️ частково (WHOIS реально; Telegram/скрапінг — каркас; профіль компанії — скрапінг без реєстрового API) |
| 5 | AI та автоматизація | ⚠️ частково (Ollama+anomaly є; AI-агенти — ні) |
| 6 | Плагінна система | ❌ (лише реєстр) |
| 7 | Безпека та деплой | ❌ |

### Додатково зроблено понад ТЗ
- **Воркспейси/дослідження** — ізоляція даних.
- **Аналіз зображень** — EXIF/GPS + зворотний геокодинг + перевірка узгодженості.
- **Кастомні AI-моделі** — будь-які OpenAI-сумісні/локальні через налаштування.
- **Профіль компанії** — агрегація вебу + парсинг сторінок + прямий запит у реєстри.
- **Redesign UI** — бокове меню, картка компанії на весь екран, міні-карта, маркери.

---

## 5. Що НЕ реалізовано / наступні кроки

- **Пошуковий API (платний):** безкоштовних пошукових API зараз немає. Стабільний пошук потребує платного ключа (Serper/Brave/інші). Зараз — скрапінг (Bing→DDG→Playwright) + кеш + троттлінг, але він впирається в rate limit пошуковиків.
- **OpenDataBot (платний):** заглушка готова (`OPENDATABOT_API_KEY`). Без нього юридичні дані компанії — лише зі скрапінгу відкритих агрегаторів (часткові).
- Реальні ключі для Shodan / Google Maps (mock).
- Скрапінг соцмереж (реальна інтеграція Playwright + ToS).
- AI-агенти на базі browser automation (фаза 5).
- Плагінна система адаптерів (фаза 6).
- Шифрування API-ключів (`ai_providers.api_key` у відкритому вигляді).
- Rate limiting адаптерів (spec §9).
- Автентифікація / профіль користувача (OAuth2/Keycloak).
- Reverse image search (TinEye/Google/Yandex).
- Пагінація списків.
- Продакшен-деплой (Kubernetes, моніторинг).

---

## 6. Як запустити

```bash
# База (опційно, SQLite працює без неї)
docker compose up -d

# Backend
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate.bat
pip install -r requirements.txt
playwright install chromium       # для browser-автоматизації
uvicorn app.main:app --reload     # http://127.0.0.1:8000

# Frontend
cd frontend
npm install
npm run dev                       # http://localhost:5173
```

---

## 7. Конфігурація (`backend/.env.example`)

| Змінна | Опис |
|--------|------|
| `DATABASE_URL` | SQLite (дефолт) або PostgreSQL |
| `SHODAN_API_KEY` / `SHODAN_MOCK` | Shodan (платний) |
| `GOOGLE_MAPS_API_KEY` / `GOOGLE_MAPS_MOCK` | Google Maps (платний) |
| `WHOIS_MOCK` | RDAP (реальний за замовчуванням) |
| `TELEGRAM_BOT_TOKEN` / `TELEGRAM_MOCK` | Telegram |
| `GOOGLE_CSE_API_KEY` / `GOOGLE_CSE_ID` | Google Custom Search (платний) |
| `BRAVE_SEARCH_API_KEY` | Brave Search API (платний) |
| `OPENDATABOT_API_KEY` | OpenDataBot (платний, реєстр компаній) |
| `ANTHROPIC_API_KEY` / `ANTHROPIC_MOCK` | Claude |
| `OPENAI_API_KEY` / `OPENAI_MODEL` | OpenAI / сумісні |
| `AI_PROVIDER` | auto / ollama / claude / openai / mock |
| `OLLAMA_BASE_URL` / `OLLAMA_MODEL` / `OLLAMA_VISION_MODEL` | локальні моделі |
| `CORS_ORIGINS` | дозволені origin |

Frontend (Mapillary): `VITE_MAPILLARY_TOKEN` у `frontend/.env`.
