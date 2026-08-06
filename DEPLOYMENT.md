# Deployment Guide

## Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- Git
- 4GB RAM minimum
- 10GB disk space

## Local Deployment

### 1. Clone Repository

```bash
git clone <repository-url>
cd kspdb-fault-detection
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` if needed (optional for local development):
```
DATABASE_URL=postgresql://kspdb:kspdb_password@db:5432/kspdb
ENVIRONMENT=development
OPENAI_API_KEY=your_key_if_using_ai_features
```

### 3. Start Services

```bash
docker compose up
```

This will:
- Start PostgreSQL database
- Start FastAPI backend on port 8000
- Start React frontend on port 3000
- Seed database with synthetic network on startup

### 4. Verify Deployment

Open http://localhost:3000 in your browser.

You should see:
- Operator Console with ticket list
- Simulator tab available
- Network stats showing seeded data

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| DATABASE_URL | No | postgresql://kspdb:kspdb_password@db:5432/kspdb | PostgreSQL connection string |
| ENVIRONMENT | No | development | Environment name |
| OPENAI_API_KEY | No | (empty) | OpenAI API key for AI summaries |

## Troubleshooting

### Port Conflicts

**Symptom:** `Error: bind: address already in use`

**Fix:** Change ports in `docker-compose.yml`:
```yaml
backend:
  ports:
    - "8001:8000"  # Change 8000 to 8001
frontend:
  ports:
    - "3001:3000"  # Change 3000 to 3001
```

### Database Connection Issues

**Symptom:** Backend logs show `connection refused` to database

**Fix:** Ensure database is healthy before backend starts:
```bash
docker compose up db
# Wait for "database system is ready to accept connections"
docker compose up backend frontend
```

### Migration Issues

**Symptom:** Tables not created on startup

**Fix:** Manual table creation:
```bash
docker compose exec backend python -c "from database import engine, Base; Base.metadata.create_all(bind=engine)"
```

### ARM vs x86 Image Issues

**Symptom:** `exec format error` on Apple Silicon

**Fix:** Use platform-specific images in `docker-compose.yml`:
```yaml
services:
  db:
    platform: linux/amd64
  backend:
    platform: linux/amd64
```

### Memory Limits on Free Tiers

**Symptom:** Container crashes with OOM

**Fix:** Add memory limits in `docker-compose.yml`:
```yaml
services:
  backend:
    mem_limit: 1g
  db:
    mem_limit: 512m
```

### CORS Issues

**Symptom:** Frontend can't connect to backend

**Fix:** CORS is already configured in `main.py`. If still failing, check:
- Backend URL in frontend `.env`: `VITE_API_URL=http://localhost:8000`
- Backend CORS middleware allows frontend origin

### WebSocket/Proxy Issues

**Symptom:** Real-time updates not working

**Fix:** This system uses polling (10s), not WebSockets. No proxy configuration needed.

### Cold-Start Timeouts

**Symptom:** Free tier takes 30+ seconds to respond

**Fix:** Add health check in `docker-compose.yml`:
```yaml
backend:
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
    interval: 30s
    timeout: 10s
    retries: 3
```

## Reset to Clean State

```bash
docker compose down -v
docker compose up
```

This removes all volumes and re-seeds the database.

## Production Deployment

### Railway/Render/Heroku

1. Push code to GitHub
2. Connect repository to platform
3. Set environment variables in platform dashboard
4. Deploy

**Note:** Free tiers may have cold-start delays. Document this in README.

### Self-Hosted VPS

```bash
# Install Docker
curl -fsSL https://get.docker.com | sh

# Clone and deploy
git clone <repo>
cd kspdb-fault-detection
docker compose up -d
```

Add reverse proxy (nginx) for SSL and domain.

## Verification Checklist

- [ ] `docker compose up` completes without errors
- [ ] Frontend loads at http://localhost:3000
- [ ] Backend API responds at http://localhost:8000/health
- [ ] Database seeded with poles and transformers
- [ ] Can inject fault from Simulator
- [ ] Ticket appears in Console
- [ ] Can repair fault from Simulator
- [ ] Ticket auto-verifies

## Performance Testing

### Test Ingest Throughput

```bash
# Install Apache Bench
ab -n 1000 -c 10 -p telemetry.json -T application/json http://localhost:8000/api/telemetry/
```

### Test Fault Detection Latency

1. Inject fault from Simulator
2. Note timestamp
3. Check Console for ticket appearance
4. Should be < 120 seconds

## Monitoring

### Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f backend
docker compose logs -f db
```

### Database Size

```bash
docker compose exec db psql -U kspdb -d kspdb -c "SELECT pg_size_pretty(pg_database_size('kspdb'));"
```

## Backup and Restore

### Backup

```bash
docker compose exec db pg_dump -U kspdb kspdb > backup.sql
```

### Restore

```bash
cat backup.sql | docker compose exec -T db psql -U kspdb kspdb
```
