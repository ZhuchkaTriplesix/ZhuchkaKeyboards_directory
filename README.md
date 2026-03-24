# ZhuchkaKeyboards directory

Microservice based on [Reei-dp/fastapi-template](https://github.com/Reei-dp/fastapi-template) (upstream systemd unit removed; includes **GitHub Actions** CI: pytest + Docker build on push/PR to `dev` / `main`).


A production-ready FastAPI boilerplate designed for rapid project setup — featuring clean architecture, Docker support, logging and INI-based configuration.

Customer directory API (see monorepo `docs/microservices/02-directory.md`): **`GET/PATCH /api/v1/me`**, **`GET/POST/PATCH/DELETE /api/v1/me/addresses`**, **`GET/POST /api/v1/me/consents`**, **`GET/POST/DELETE /api/v1/me/b2b-links`** require a **Bearer** access token from Auth (`RS256`); configure **`[AUTH]`** in `config.ini` (`JWKS_URL`, `ISSUER`, `AUDIENCE` must match the authorization server). The first successful `GET /me` creates a profile row keyed by JWT `sub`. At most one address per customer may be marked **default** (`is_default`); setting it clears `is_default` on other rows. Consents are stored per **privacy** / **marketing** with **document version**; `GET /me/consents` returns only active rows (not withdrawn). **B2B links** store **`counterparty_id`** (UUID in counterparties service) and **`contact_role`** per customer; duplicate pair returns **409**.

**Operational (staff):** same Bearer token; JWT **`scope`** must include **`support.read`** or **`support.write`** or **`admin`** for **`GET /api/v1/customers`** and **`GET /api/v1/customers/{id}`**; **`support.write`** or **`admin`** for **`PATCH`** and **`POST …/merge`**. **`GET /customers`** supports optional **`counterparty_id`**. **`PATCH`** uses the same body as **`PATCH /me`**; duplicate email returns **409** `email_already_exists`. **`merge`** body: `{ "into_customer_id": "<uuid>" }` — moves addresses, consents, and B2B links into the target, then deletes the source customer.

**Integration events (outbox):** rows in **`outbox_event`** with types **`directory.customer.created`**, **`directory.customer.updated`**, **`directory.consent.changed`** (JSON payload; published by a separate worker — not part of this service yet).

## Features

- ⚡ **FastAPI** with Python 3.13
- 🐳 **Docker** & **Docker Compose** for development and production
- 🗄️ **PostgreSQL** database with SQLAlchemy
- 🔴 **Redis** for caching
- 🔒 **Nginx** reverse proxy with rate limiting
- 📝 **Alembic** for database migrations
- 🧪 **Pytest** for testing
- 📊 **Logging** configured and ready to use
- 🔧 **Makefile** for convenient development
- 🔄 **GitHub Actions**: pytest + Docker build (`.github/workflows/ci.yml`)

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.13+ (for local development)
- Make (optional)

### Installation

1. Clone the repository:
```bash
git clone <your-repo-url>
cd ZhuchkaKeyboards_directory
```

2. Create `config.ini` file from example:
```bash
cp config.ini.example config.ini
```

3. Edit `config.ini` file according to your needs

### Running (Development)

#### Using Docker Compose:
```bash
make dev
# or
docker compose -f docker/docker-compose.dev.yml up --build
```

#### Locally (without Docker):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python src/main.py
# or
uvicorn src.main:app --reload
```

Application will be available at: http://localhost:8000

API documentation:
- Swagger UI: http://localhost:8000/api/docs (HTTP Basic — same placeholder `USERNAME` / `PASSWORD` as in `src/main.py`)
- OpenAPI JSON: http://localhost:8000/api/openapi.json (same Basic auth; not publicly exposed without credentials)
- OpenAPI tags separate **Customer (self)** (`/me`, …) from **Customer (staff)** (`/customers`, …).

**Observability:** **`GET /metrics`** — Prometheus exposition (process metrics; scrape from your stack). **`X-Request-ID`** — optional incoming header (alphanumeric, dots, underscores, hyphens, max 128 chars); if absent or invalid, a UUID is generated; the chosen value is always returned on the response. Application logs use the format **`[req=<id>]`** when a request id is in context (requires **`src.main:app`** so HTTP middleware is registered).

### Running (Production)

```bash
make up
# or
docker compose -f docker/docker-compose.yml up -d
```

## Project Structure

```
ZhuchkaKeyboards_directory/
├── src/                          # Source code
│   ├── main.py                   # FastAPI application entry point
│   ├── config.py                 # Configuration loader (INI files)
│   ├── dependencies.py           # Global dependencies
│   ├── schemas.py                # Shared Pydantic schemas
│   ├── configuration/
│   │   └── app.py                # FastAPI app initialization
│   ├── middlewares/              # HTTP middlewares
│   │   ├── __init__.py
│   │   ├── request_id.py         # X-Request-ID + logging context
│   │   └── database.py           # Database session per request
│   ├── routers/                  # API routers
│   │   ├── __init__.py           # Router registration
│   │   └── root/                 # Root endpoints
│   │       ├── router.py         # Route definitions
│   │       ├── actions.py        # Business logic
│   │       ├── dal.py            # Data access layer
│   │       ├── models.py         # Database models
│   │       └── schemas.py        # Request/response schemas
│   ├── database/                 # Database configuration
│   │   ├── core.py               # Database engine and sessions
│   │   ├── base.py               # Base model class
│   │   ├── dependencies.py       # Database dependencies
│   │   ├── logging.py            # Session tracking
│   │   └── alembic/              # Database migrations
│   ├── redis_client/             # Redis operations
│   │   └── redis.py              # Redis controller with caching methods
│   ├── services/                 # External service integrations
│   └── misc/                     # Utilities
│       ├── security.py           # Security utilities
│       └── timezone.py           # Timezone utilities
├── docker/
│   ├── Dockerfile                # Production Dockerfile
│   ├── Dockerfile.dev            # Development Dockerfile
│   ├── docker-compose.yml        # Production stack
│   ├── docker-compose.dev.yml    # Development stack
│   └── nginx/
│       └── nginx.conf            # Nginx configuration
├── config.ini.example            # Configuration template
├── alembic.ini.example           # Alembic configuration template
├── requirements.txt              # Python dependencies
├── Makefile                      # Build commands
├── start.sh                      # Startup script
└── README.md                     # This file
```

## Makefile Commands

```bash
make help           # Show all available commands
make install        # Install dependencies
make dev            # Start development environment
make build          # Build production Docker image
make up             # Start production environment
make down           # Stop all containers
make logs           # Show logs
make clean          # Remove containers and volumes
make test           # Run tests
make lint           # Run linter
make format         # Format code
make migrate        # Apply migrations
make migrate-create # Create new migration
```


## Configuration

Application uses INI files for configuration (see `config.ini.example`):

```ini
[POSTGRES]
# PostgreSQL database configuration
DATABASE = postgresql
DRIVER = asyncpg
DATABASE_NAME = your_database_name
USERNAME = postgres
PASSWORD = your_password
IP = localhost
PORT = 5432

# Connection pool settings
DATABASE_ENGINE_POOL_TIMEOUT = 30
DATABASE_ENGINE_POOL_RECYCLE = 3600
DATABASE_ENGINE_POOL_SIZE = 5
DATABASE_ENGINE_MAX_OVERFLOW = 10
DATABASE_ENGINE_POOL_PING = true

# Database echo (SQL logging) - set to false in production
DATABASE_ECHO = false

[UVICORN]
# Uvicorn server configuration
HOST = 0.0.0.0
PORT = 8000
WORKERS = 4
LOOP = uvloop          # Event loop: asyncio | uvloop (uvloop is faster)
HTTP = httptools       # HTTP protocol: h11 | httptools (httptools is faster)

[REDIS]
# Redis cache configuration
HOST = localhost
PORT = 6379
DB = 0
PASSWORD =
```

### Key Features

#### Database Middleware
- Automatic session management per request
- Auto-commit on success, rollback on error
- Session tracking for debugging
- Request ID generation for tracing

#### Redis Client
- Simple caching interface with `get()`, `set()`, `delete()`, `update()`
- JSON serialization support with `get_json()` and `set_json()`
- TTL (Time To Live) management
- Multiple key deletion support

#### Health checks
- **`GET /health/live`** — liveness (process up, no dependencies)
- **`GET /health/ready`** — readiness (database reachable)
- **`GET /api/root/health`** — full check: database + Redis; returns 200 or 503


## Testing

```bash
pip install -r requirements.txt -r requirements-dev.txt
make test
```

`requirements-dev.txt` adds **pytest**, **pytest-cov**, and **ruff** (same pattern as `make lint` / `make format`). For coverage only: `pytest tests/ -v --cov=src --cov-report=html`.

If `config.ini` is missing locally, `tests/conftest.py` copies `config.ini.example` so imports from `src.config` succeed during test collection.

## Development

### Creating new migration:
```bash
make migrate-create
# or
alembic revision --autogenerate -m "migration description"
```

### Applying migrations:
```bash
make migrate
# or
alembic upgrade head
```

### Code formatting:
```bash
make format
```

## License

MIT License - see [LICENSE](LICENSE) file
