# Deployment Guide

This guide covers different deployment methods for your FastAPI application.

## Table of Contents

- [Configuration](#configuration)
- [Docker Deployment](#docker-deployment)
- [Health](#health)
- [Production Checklist](#production-checklist)

## Configuration

- **Application and database settings** — single file **`config.ini`** (see [`config.ini.example`](config.ini.example) and [docs/CONFIGURATION.md](docs/CONFIGURATION.md)). Mount or generate this file per environment; there is no `.env` loader in code.
- **JWT / Auth** — [docs/AUTH-JWT.md](docs/AUTH-JWT.md) describes JWKS, issuer, audience, and staff `scope` expectations.
- **Alembic** — copy `alembic.ini.example` to `alembic.ini` and run `alembic upgrade head` after deploy.

## Docker Deployment

### Using Docker Compose (Recommended)

1. **Prepare configuration files:**
```bash
cp config.ini.example config.ini
cp alembic.ini.example alembic.ini
# Edit config.ini and alembic.ini with production values
```

2. **Build and start services:**
```bash
docker compose -f docker/docker-compose.yml up -d --build
```

3. **Check service status:**
```bash
docker compose -f docker/docker-compose.yml ps
docker compose -f docker/docker-compose.yml logs -f
```

4. **Run database migrations:**
```bash
docker compose -f docker/docker-compose.yml exec fastapi-app alembic upgrade head
```

## Health

- **`GET /health/live`** — process up (no dependency checks).
- **`GET /health/ready`** — includes a database check (`SELECT 1`); use for orchestrator readiness when Postgres is required.

### Using Docker only

1. **Build image:**
```bash
docker build -f docker/Dockerfile -t fastapi-app:latest .
```

2. **Run container:**
```bash
docker run -d \
  --name fastapi-app \
  -p 8000:8000 \
  -v $(pwd)/config.ini:/app/config.ini:ro \
  -v $(pwd)/logs:/app/logs \
  fastapi-app:latest
```



## Observability

| Endpoint / behavior | Notes |
|---------------------|--------|
| `GET /metrics` | Prometheus text format (`prometheus_client`); scrape from your monitoring stack. |
| `GET /health/live`, `GET /health/ready` | Liveness / readiness (readiness checks DB). |
| `X-Request-ID` | Optional request header; echoed on the response. Invalid or missing values are replaced with a generated id. |
| Logs | Root logger format includes `[req=<id>]` when the request middleware runs (`src.main:app`). |

## Configuration file (`config.ini`)

Production values are read from **`config.ini`** at the repository root (see `config.ini.example`). There is no separate dotenv layer: copy the example, then set at least:

| Section | Keys (summary) |
|---------|----------------|
| `POSTGRES` | `DATABASE`, `DRIVER`, `DATABASE_NAME`, `USERNAME`, `PASSWORD`, `IP`, `PORT`, pool settings |
| `UVICORN` / Granian | `HOST`, `PORT`, `WORKERS`, `LOOP`, `HTTP` |
| `REDIS` | `HOST`, `PORT`, `DB`, `PASSWORD` |
| `AUTH` | `JWKS_URL`, `ISSUER`, `AUDIENCE` (must match Auth service) |

HTTP Basic credentials for `/api/docs` and `/api/openapi.json` are **placeholders in `src/main.py`** — replace for production or move to configuration.

## Production Checklist

Before deploying to production, ensure:

### Security

- [ ] Strong **database** credentials and least-privilege DB user for the service
- [ ] **`[AUTH]`** `JWKS_URL` / `ISSUER` / `AUDIENCE` point to production Auth and match issued tokens
- [ ] HTTP Basic credentials for **`/api/docs`** and **`/api/openapi.json`** in `src/main.py` replaced or removed for production (or protect behind Traefik/mTLS)
- [ ] Updated database credentials
- [ ] Configured CORS origins properly
- [ ] Set up SSL/TLS certificates for HTTPS
- [ ] Configure firewall rules (only allow 80, 443, 22)
- [ ] Disable PostgreSQL remote access if not needed
- [ ] Set strong Redis password if exposed

### Configuration

- [ ] Tune **`[POSTGRES]`** pool settings for expected load (`DATABASE_ENGINE_POOL_SIZE`, etc.)
- [ ] Configure proper database connection pooling
- [ ] Set appropriate log levels
- [ ] Configure Redis connection
- [ ] Update Nginx configuration if using custom domain
- [ ] Set proper CORS origins

### Infrastructure

- [ ] Database backups configured
- [ ] Log rotation configured
- [ ] Monitoring and alerting set up
- [ ] Health check endpoints working
- [ ] Nginx reverse proxy configured
- [ ] SSL certificates installed and renewed automatically
- [ ] Sufficient disk space allocated

### Performance

- [ ] Adjust uvicorn workers count based on CPU cores
- [ ] Configure database connection pool size
- [ ] Set up Redis for caching
- [ ] Enable gzip compression in Nginx
- [ ] Configure static file serving

### Testing

- [ ] All tests passing
- [ ] Load testing completed
- [ ] Health check endpoint responding
- [ ] Database migrations tested
- [ ] Rollback procedure tested

## Monitoring

### Health Check

The API exposes **liveness** and **readiness** probes (`src/configuration/app.py`), plus a detailed check under `/api/root`:

```bash
curl http://localhost:8000/health/live    # process up (200)
curl http://localhost:8000/health/ready   # DB reachable (200)
curl http://localhost:8000/api/root/health # DB + Redis (200 or 503)
```

Behind Nginx on port 80, `GET /health` proxies to liveness (`/health/live`).

### Logs

#### Docker:
```bash
docker compose -f docker/docker-compose.yml logs -f fastapi-app
```

#### Systemd:
```bash
sudo journalctl -u fastapi-app -f
# or
tail -f logs/app.log
```

### Service Status

#### Docker:
```bash
docker compose -f docker/docker-compose.yml ps
```

#### Systemd:
```bash
sudo systemctl status fastapi-app
```

## Rollback

### Docker Deployment

```bash
# Stop current version
docker compose -f docker/docker-compose.yml down

# Checkout previous version
git checkout <previous-commit>

# Rebuild and start
docker compose -f docker/docker-compose.yml up -d --build
```

### Systemd Deployment

```bash
# Stop service
sudo systemctl stop fastapi-app

# Checkout previous version
cd /opt/apps/fastapi-app
git checkout <previous-commit>

# Reinstall dependencies if needed
source venv/bin/activate
pip install -r requirements.txt

# Restart service
sudo systemctl start fastapi-app
```

## Scaling

### Horizontal Scaling

For load balancing multiple instances:

1. Run multiple containers on different ports
2. Configure Nginx upstream:

```nginx
upstream fastapi_cluster {
    server localhost:8000;
    server localhost:8001;
    server localhost:8002;
}
```

### Vertical Scaling

Adjust worker processes in production:

```ini
# In your start script or service file
uvicorn app.main:app --workers 8
```

Rule of thumb: `workers = (2 x CPU cores) + 1`

## Troubleshooting

### Application won't start

1. Check logs: `docker compose logs` or `journalctl -u fastapi-app`
2. Verify config.ini exists and is readable
3. Check database connectivity
4. Ensure port 8000 is not in use

### Database connection errors

1. Verify database is running
2. Check database credentials in config.ini
3. Ensure database accepts connections
4. Test connection manually: `psql -h localhost -U postgres -d fastapi_db`

### High memory usage

1. Reduce number of workers
2. Adjust database connection pool size
3. Check for memory leaks in application code
4. Monitor with `docker stats` or `htop`

## Support

For issues or questions:
- Check application logs
- Review configuration files
- Consult FastAPI documentation: https://fastapi.tiangolo.com/
- Check Docker documentation: https://docs.docker.com/

