# Task Worker - Docker Setup

This guide explains how to run the discovery task worker in Docker.

## 🚀 Quick Start (Recommended)

Run the automated setup script:

```powershell
cd d:\PROJECTS-REPOS\AFFILIATE-PROJ\affili-ai-hub\affili-ai-backend
.\setup-docker.ps1
```

This will:
- Clean old containers/images
- Build backend and worker images (no double builds!)
- Start all services
- Show service status

## Manual Setup

If you prefer manual control:

```bash
# Clean everything
docker-compose down -v
docker system prune -f

# Build (note: only builds once per service)
docker-compose build --no-cache

# Start
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker logs -f affili-ai-worker
docker logs -f affili-ai-backend
```

## Services

The docker-compose includes:

- **postgres** - PostgreSQL database (port 5432)
- **backend** - FastAPI API server (port 8000)
- **worker** - Discovery task executor with Playwright

## How It Works

The worker:
1. Polls database for `DISCOVER_PROGRAM` tasks (every 2 seconds)
2. Uses Playwright/Chromium for web scraping
3. Creates discovered programs in database
4. Updates task status: PENDING → RUNNING → COMPLETED/FAILED

## Configuration

Environment variables (from `.env`):
- `DATABASE_URL` - Shared PostgreSQL connection
- `AGENT_CLIENT_ID` - Worker identifier
- `GEMINI_API_KEY` - For AI features (optional)

## Troubleshooting

### Worker not picking up tasks

```bash
# Check worker logs for errors
docker logs affili-ai-worker

# Restart worker
docker-compose restart worker
```

### "Two builds" issue - FIXED!

Previously, Docker would build images twice. Now fixed by:
- Explicit `image:` names in docker-compose.yml
- Each service builds only once and caches the result

### Rebuild after code changes

```bash
# Rebuild specific service
docker-compose build worker
docker-compose up -d worker

# Or rebuild everything
.\setup-docker.ps1
```

## Development

For local development without Docker:

```bash
cd affili-ai-backend
venv\Scripts\activate
python scripts/run_worker.py
```

Useful for debugging, but Docker is recommended for testing.
