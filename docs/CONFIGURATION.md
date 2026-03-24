# Configuration (`config.ini`)

The service reads **`config.ini`** in the repository root (same directory as `src/`). There is **no** built-in override from environment variables; use a file mount in Docker/Kubernetes or generate the file from your secret store.

Copy from the template:

```bash
cp config.ini.example config.ini
```

## Sections

### `[POSTGRES]`

| Key | Meaning |
|-----|---------|
| `DATABASE` | SQLAlchemy dialect name (e.g. `postgresql`). |
| `DRIVER` | Async driver (`asyncpg`). |
| `DATABASE_NAME` | Database name. |
| `USERNAME` / `PASSWORD` | Credentials. |
| `IP` / `PORT` | Host and port of PostgreSQL. |
| `DATABASE_ENGINE_*` | Pool timeout, recycle, size, overflow, pre-ping, echo — see `config.ini.example`. |

Connection URL shape: `{DATABASE}+{DRIVER}://{USERNAME}:{PASSWORD}@{IP}:{PORT}/{DATABASE_NAME}`.

### `[UVICORN]` (Granian)

Legacy section name; used by **`run_granian_app`** in `src/config.py`: bind address, port, worker count, event loop (`LOOP`), HTTP mode (`HTTP`).

### `[REDIS]`

Host, port, DB index, password — used by Redis helpers when enabled.

### `[AUTH]`

| Key | Meaning |
|-----|---------|
| `JWKS_URL` | Full URL to the Auth service JWKS document (e.g. `https://auth.example.com/.well-known/jwks.json`). |
| `ISSUER` | JWT `iss` claim; must match tokens issued by Auth (no trailing slash mismatch: code normalizes issuer). |
| `AUDIENCE` | JWT `aud` claim; must match the API audience configured in Auth for this resource server. |

See [AUTH-JWT.md](AUTH-JWT.md) for the token contract.

## Alembic

Database migrations use **`alembic.ini`** (copy from `alembic.ini.example`). Run migrations after changing DB or deploying new versions:

```bash
alembic upgrade head
```
