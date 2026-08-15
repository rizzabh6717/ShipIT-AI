# ShipIT — AI-Powered Logistics Platform

ShipIT connects **senders** who need parcels shipped with **drivers** who have planned routes and spare capacity. The platform uses an explainable AI matching pipeline — powered by pgvector semantic similarity + optional LLM re-ranking (OpenRouter/OpenAI) — to pair every parcel with the best driver and explain *why*.

```
Sender creates parcel  ─┐
                        ├─►  AI MATCHING PIPELINE  ─►  ranked, explainable driver matches
Driver publishes route ─┘             │
                                      ▼
                       Driver accepts → picks up → delivers (with proof upload)
```

---

## 1. Tech Stack

| Layer        | Technology                                                        |
|--------------|-------------------------------------------------------------------|
| Language     | Python 3.13                                                       |
| API framework| FastAPI + Uvicorn (async)                                         |
| ORM          | SQLAlchemy 2.0 (async, `asyncpg` driver)                          |
| Database     | PostgreSQL 18                                                     |
| Vector search| pgvector 0.8.6 — `vector(1536)` column + **HNSW** cosine index   |
| Embeddings   | OpenRouter or OpenAI (`text-embedding-3-small`) — **offline deterministic fallback** |
| LLM ranking  | LangChain (`langchain-openai`) → OpenRouter / OpenAI — **heuristic fallback** |
| Auth         | JWT (PyJWT, HS256) + bcrypt password hashing                      |
| Migrations   | Alembic                                                           |
| Uploads      | `aiofiles` (local disk, served via StaticFiles)                   |
| Tests        | pytest + pytest-asyncio + httpx (`ASGITransport`)                 |

> **No-API-key mode:** with `EMBEDDING_PROVIDER=deterministic` and `LLM_PROVIDER=heuristic` (the defaults), the **entire pipeline runs offline** — embeddings are feature-hash vectors and ranking is a fully explainable weighted heuristic. Set API keys to switch to real semantic embeddings and LLM ranking.

---

## 2. Project Layout

```
backend/
├── alembic.ini                 # Alembic config (URL injected at runtime)
├── requirements.txt            # Python dependencies
├── pytest.ini                  # pytest / asyncio configuration
├── .env.example                # Environment template (copy to .env)
├── alembic/
│   ├── env.py                  # Sync engine from settings.database_url_sync
│   ├── script.py.mako
│   └── versions/0001_initial.py# Full schema + vector extension + HNSW index
├── tests/
│   ├── conftest.py             # Isolated shipit_test DB + async HTTP client
│   ├── test_auth.py            # Registration, login, JWT, exists-check
│   ├── test_parcels.py         # Parcel CRUD + delivery workflow
│   └── test_matching.py        # Route embedding + AI match pipeline
└── app/
    ├── main.py                 # FastAPI app: lifespan, CORS, routers, /uploads mount
    ├── config.py               # Pydantic Settings (env-driven)
    ├── database.py             # Async engine + AsyncSessionLocal + Base
    ├── dependencies.py         # get_session, get_current_user, require_roles
    ├── models/                 # SQLAlchemy ORM models
    ├── schemas/                # Pydantic request/response models
    ├── services/               # Business logic layer
    ├── routers/                # HTTP endpoints (one per domain)
    ├── ai/                     # Embeddings, vector store, explainer, matcher
    └── utils/                  # security (bcrypt/JWT), geo, public_ids
```

---

## 3. Data Model

```
users (1) ──(1)── drivers (1) ──(n)── routes
   │                                    │  route_embedding vector(1536) ← HNSW index
   │
   └──(n)── parcels (1) ──(1)── deliveries
                │                        │
                └──(n)── matches (n)─────┘  ← persisted AI match (score, eta, explanation)
```

| Table       | Key columns                                                                                          |
|-------------|------------------------------------------------------------------------------------------------------|
| `users`     | `public_id` (U…), `email` (unique), `password_hash`, `role` (sender/driver/admin), `is_active`       |
| `drivers`   | `public_id` (D…), `user_id` (unique 1:1), `vehicle_type`, `capacity_kg`, `rating`, `on_time_rate`, `status` (available/busy/offline), `current_city` |
| `routes`    | `driver_id`, `origin`, `destination`, `waypoints` (JSON), `route_text`, **`route_embedding vector(1536)`**, `is_active`, `planned_at` |
| `parcels`   | `public_id` (P…), `sender_id`, `pickup_location`, `drop_location`, `item_description`, `weight`, `budget`, `deadline`, `size_tier`, `status` (pending → … → delivered/cancelled) |
| `deliveries`| `public_id` (DLV…), `parcel_id` (unique), `driver_id`, `accepted_at`, `picked_up_at`, `delivered_at`, `proof_image_url` |
| `matches`   | `parcel_id` + `driver_id` (unique pair), `match_score`, `eta`, `explanation` (newline-separated reasons) |

**Public IDs** (`app/utils/public_ids.py`) decouple API-facing identifiers from integer primary keys to prevent ID enumeration: `U…`, `D…`, `P…`, `DLV…`.

---

## 4. Authentication & Security

- **Passwords:** bcrypt (`hash_password` / `verify_password` in `app/utils/security.py`).
- **Tokens:** signed JWT, HS256, claims `sub` (user public_id), `role`, `iat`, `exp` (default 60 min).
- **Flow:** register → server returns `{access_token, user}` → client sends `Authorization: Bearer <token>`.
- **Endpoints:** register sender, register driver (creates the linked `Driver` profile in one transaction), login, `/auth/me`, and a frontend-compat `GET /auth/user/{public_id}` "does this account exist?" check.
- **Role guards:** `dependencies.require_roles(*roles)` protects admin-only routes; drivers-only actions check `user.role`.

---

## 5. AI Matching Pipeline (the core)

`POST /api/ai/match` (`app/services/matching_service.py`)

```
 1. Build parcel text            parcel_to_text(parcel) — normalized textual fingerprint
 2. Embed the query              embedder.embed([parcel_text])  → 1536-d vector
 3. Candidate retrieval          pgvector cosine search over active routes:
                                  Route.route_embedding.cosine_distance(q)  (HNSW, top_k)
                                └─ fallback: token-overlap search if no embeddings exist yet
 4. Build candidates             (driver, route, similarity, pickup detour via geo utils)
 5. Rank
        ├─ LLM mode   (LLM_PROVIDER=openrouter/openai + API key):
        │            LangChain ChatOpenAI → structured JSON ranking,
        │            considers route overlap, detour, deadline, reliability, capacity
        └─ Heuristic (default) fully explainable weighted score:
                0.35 route overlap  + 0.15 pickup proximity
              + 0.15 deadline      + 0.20 reliability (rating & on-time)
              + 0.15 capacity
 6. Persist                      upsert into matches (score, eta, explanation)
 7. Respond                      ranked matches with human-readable reasons + ETA
```

### Explainability
Every match carries a `reason` list, e.g.:

```
Route overlap: 43%
Pickup detour: 0.0 km
Delivery deadline: 24.0h away
Vehicle capacity sufficient (10.0kg of 800kg)
Driver reliability: 5.0/5
On-time rate: 100%
```

These are produced deterministically by `app/ai/explainer.py` in both modes, so the API is explainable even without an LLM.

### Geo estimation
`app/utils/geo.py` uses haversine distance when lat/lng waypoints exist, otherwise a normalized token-overlap heuristic — no geocoding dependency required.

### Embedding providers (`app/ai/embeddings.py`)
| Provider        | When                                             | Notes                                  |
|-----------------|--------------------------------------------------|----------------------------------------|
| `deterministic` | no `EMBEDDING_API_KEY` (default)                 | feature-hash vectors, offline, stable   |
| `openrouter`    | `EMBEDDING_PROVIDER=openrouter` + key            | any OpenRouter embedding model         |
| `openai`        | `EMBEDDING_PROVIDER=openai` + key                | e.g. `text-embedding-3-small`          |

---

## 6. End-to-End Flow

```
DRIVER:                                  SENDER:
  POST /auth/register/driver               POST /auth/register/sender
  POST /drivers/me/availability            POST /parcels            {pickup, drop, weight, ...}
  POST /routes          {origin, destination}            │
      └ auto-embeds route into pgvector                   ▼
                              POST /ai/match  {parcel_id}
                              └─ returns ranked explainable matches
                                     │
                                     ▼  driver views available parcels
  POST /deliveries/accept?parcel_id=P… ─►  parcel.status = accepted, driver.status = busy
  POST /deliveries/{DLV…}/pickup       ─►  status = picked_up
  POST /deliveries/{DLV…}/delivered    ─►  status = delivered, driver.status = available
  POST /photos/delivery-proof          ─►  proof_image_url attached
```

Parcel status lifecycle: `pending → matched → accepted → picked_up → in_transit → delivered` (or `cancelled`). Creating/duplicate accepts are rejected (`409`).

---

## 7. API Reference

Base URL: `http://localhost:8000/api` — interactive docs at `/docs` (Swagger) and `/redoc`.

| Method | Path                              | Auth   | Description                                    |
|--------|-----------------------------------|--------|------------------------------------------------|
| POST   | `/auth/register/sender`           | –      | Register sender → JWT + user                   |
| POST   | `/auth/register/driver`           | –      | Register driver (+ profile) → JWT + user       |
| POST   | `/auth/login`                     | –      | Email+password → JWT                           |
| GET    | `/auth/me`                        | Bearer | Current user                                   |
| GET    | `/auth/user/{public_id}`          | –      | Frontend "does account exist?" check           |
| GET/PATCH | `/users/me`                   | Bearer | Get / update profile                           |
| GET    | `/users/{public_id}`              | Admin  | Look up a user                                 |
| GET    | `/drivers/me`                     | Bearer | Driver profile (auto-created if missing)       |
| PATCH  | `/drivers/me`                     | Bearer | Update profile                                 |
| PATCH  | `/drivers/me/availability`        | Bearer | Set status + current city                      |
| GET    | `/drivers`                        | –      | List available drivers (filter by `city`)      |
| GET    | `/drivers/{public_id}`            | –      | Driver detail                                  |
| POST   | `/parcels`                        | Bearer | Create parcel                                  |
| GET    | `/parcels`                        | Bearer | Own parcels                                    |
| GET    | `/parcels/available`              | Bearer | Parcels needing a driver (pending/matched)     |
| GET    | `/parcels/{public_id}`            | Bearer | Parcel detail + persisted matches + best_driver|
| PATCH  | `/parcels/{public_id}`            | Owner  | Update parcel                                  |
| POST   | `/parcels/{public_id}/cancel`     | Owner  | Cancel parcel                                  |
| POST   | `/routes`                         | Driver | Create route (auto-embeds)                     |
| GET    | `/routes/me`                      | Driver | My routes (`has_embedding` flag)               |
| POST   | `/routes/me/embed`                | Driver | Re-embed all active routes                     |
| POST   | `/routes/embed`                   | Driver | Embed by id or create+embed on the fly         |
| POST   | `/deliveries/accept?parcel_id=`   | Driver | Accept a parcel                                |
| POST   | `/deliveries/{id}/pickup`         | Driver | Confirm pickup                                 |
| POST   | `/deliveries/{id}/delivered`      | Driver | Mark delivered                                 |
| GET    | `/deliveries/driver/me`           | Driver | My deliveries                                  |
| GET    | `/deliveries/{public_id}`         | Driver | Delivery detail (owner only)                   |
| POST   | `/photos/upload-sender-photo`     | Bearer | Upload parcel photo (jpeg/png/webp)            |
| POST   | `/photos/delivery-proof`          | Driver | Upload proof, attaches to delivery             |
| POST   | `/ai/match`                       | Bearer | Run matching pipeline: `{"parcel_id":"P…"}`    |
| GET    | `/ai/matches/{parcel_id}`         | Bearer | Last persisted matches                         |
| GET    | `/ai/status`                      | Bearer | Which embedding/LLM providers are active       |
| GET    | `/health`                         | –      | Liveness probe                                 |

---

## 8. Environment Configuration

Copy `.env.example` → `.env` and adjust. All values have safe defaults so the app runs out of the box.

| Variable                  | Default                                              | Purpose                              |
|---------------------------|------------------------------------------------------|--------------------------------------|
| `DATABASE_URL`            | `postgresql+asyncpg://postgres:22058@localhost:5432/shipit` | Async Postgres connection       |
| `JWT_SECRET_KEY`          | `change-me-to-a-long-random-secret`                  | **Change in production**             |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60`                                              | JWT lifetime                         |
| `CORS_ORIGINS`            | `["http://localhost:5173","http://127.0.0.1:5173"]`  | Frontend origins                     |
| `UPLOAD_DIR`              | `./uploads`                                          | Local upload storage                 |
| `EMBEDDING_PROVIDER`      | `deterministic`                                      | `openrouter` \| `openai` \| `deterministic` |
| `EMBEDDING_MODEL`         | `text-embedding-3-small`                             | Embedding model                      |
| `EMBEDDING_DIMENSIONS`    | `1536`                                               | Vector dimension (must match DB)     |
| `EMBEDDING_API_KEY`       | *(empty)*                                            | Key for real embeddings              |
| `EMBEDDING_BASE_URL`      | `https://openrouter.ai/api/v1`                       | OpenAI-compatible endpoint           |
| `LLM_PROVIDER`            | `heuristic`                                          | `openrouter` \| `openai` \| `heuristic` |
| `LLM_MODEL`               | `meta-llama/llama-3.1-8b-instruct`                   | Ranking model                        |
| `LLM_API_KEY`             | *(empty)*                                            | Key for LLM ranking                  |
| `LLM_BASE_URL`            | `https://openrouter.ai/api/v1`                       | OpenAI-compatible endpoint           |
| `AI_MATCH_TOP_K`          | `10`                                                 | Candidates retrieved                 |
| `AI_MATCH_MAX_RESULTS`    | `5`                                                  | Matches returned/persisted           |

---

## 9. Setup & Running

### Prerequisites
- Python 3.13
- PostgreSQL 18 **with the pgvector extension installed** (Windows: copy `vector.dll` → `…/lib/` and `vector*.sql` + `vector.control` → `…/share/extension/`, then restart the service).
- Two databases (or create the second): `shipit` (app) and `shipit_test` (tests).

### Steps
```bash
cd backend

# 1. Virtualenv + dependencies
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt

# 2. Environment
copy .env.example .env          # then edit values

# 3. Create the schema (includes pgvector extension + HNSW index)
alembic upgrade head

# 4. Run the server
uvicorn app.main:app --reload
```

Server is at `http://localhost:8000`, API docs at `http://localhost:8000/docs`.

### Migrations
```bash
alembic revision --autogenerate -m "describe change"   # generate (needs live DB)
alembic upgrade head                                    # apply
alembic downgrade base                                  # rollback
```

### Tests
```bash
pytest tests -q
```
The suite recreates every table in `shipit_test` per run — **it never touches the `shipit` dev database**. It verifies auth, parcel CRUD, the full accept→pickup→deliver workflow, route embedding, and the explainable AI match pipeline.

---

## 10. Extending / Scaling Notes

- **Indexing:** routes use an HNSW index (`vector_cosine_ops`). For very large route counts, tune `ef_construction`/`m` or switch to `ivfflat`.
- **LLM mode:** set `LLM_PROVIDER` + `LLM_API_KEY` and `EMBEDDING_PROVIDER` + `EMBEDDING_API_KEY` to use real embeddings and LLM ranking; re-run `POST /routes/me/embed` to re-embed existing routes.
- **Uploads:** currently local disk (`UPLOAD_DIR`). Swap `_save_upload` for S3/cloud storage in production and serve via CDN.
- **Background work:** embedding on route creation is synchronous; for scale, move it to a task queue (Celery/RQ) and mark routes `is_active=false` until embedded.
- **Deadline/geocoding:** add real geocoding to populate waypoint lat/lng — `app/utils/geo.py` already uses haversine when coordinates are present.
