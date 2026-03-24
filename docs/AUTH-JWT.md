# Auth / JWT contract (directory service)

Directory validates **OAuth2 access tokens** issued by **Zhuchka Auth** (`services/auth`). It does **not** implement login; it only verifies JWTs using **JWKS** (RS256).

## Validation rules

- **Algorithm:** `RS256`.
- **Claims required by the verifier:** `exp`, `sub`, `iss`, `aud`, and `token_use` must be `access`.
- **`sub`:** UUID string — logical user id; maps 1:1 to a `Customer` row (lazy-created on first `/api/v1/me`).
- **`iss` / `aud`:** Must match **`[AUTH]`** in `config.ini` (`ISSUER`, `AUDIENCE`) and the values Auth puts on tokens.

Configuration keys: `JWKS_URL`, `ISSUER`, `AUDIENCE` — see [CONFIGURATION.md](CONFIGURATION.md).

## Scopes (staff)

| Surface | Requirement |
|--------|---------------|
| **Self-service** `/api/v1/me`, `/me/addresses`, `/me/consents`, `/me/b2b-links` | Valid Bearer access token; no extra scope checked in this service beyond successful JWT validation. Product policy may require `profile` / `customer` on the Auth client — enforce in Auth and document for clients. |
| **Staff** `GET /api/v1/customers`, `GET /api/v1/customers/{id}` | JWT **`scope`** (space-separated) includes **`admin`** or **`support.read`** or **`support.write`**. Returns **403** `insufficient_scope` otherwise. |
| **Staff** `PATCH /api/v1/customers/{id}`, `POST …/merge` | **`admin`** or **`support.write`**. |

The Auth bootstrap OAuth client should list `support.read` and `support.write` in **allowed_scopes** if you mint staff tokens from that client.

## Operational notes

- Rotate signing keys in Auth; JWKS is fetched by **`PyJWKClient`** (caching behaviour is library-defined).
- For local development, point `JWKS_URL` / `ISSUER` / `AUDIENCE` at the same Auth instance that mints your test tokens (see monorepo `docker/auth/config.dev.ini` if using the shared stack).
