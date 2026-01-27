# AFFILI-AI Backend

A production-quality FastAPI monolith for automated affiliate marketing. Orchestrates browser automation agents, manages affiliate programs, and processes applications at scale.

**Status:** MVP-ready | **Version:** 1.0.0

## Overview

AFFILI-AI backend provides a centralized orchestration platform for affiliate marketing automation:

- **FastAPI Monolith**: Type-safe REST API with automatic documentation
- **Task Queue**: Agent-based task dispatcher for distributed Playwright automation
- **Credential Encryption**: AES-256-GCM envelope encryption for API keys and secrets
- **Vector Search**: Response pool with pgvector support for Q&A similarity search (optional)
- **PostgreSQL/Supabase**: Serverless database backing with automatic migrations

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 13+ (or Supabase account)
- Git

### 1. Setup Virtual Environment

```bash
cd affili-ai-backend
python -m venv venv

# On Windows:
.\venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env with your settings
```

### 4. Setup Database

For **Supabase**:
1. Create a Supabase project
2. Go to SQL Editor
3. Copy contents of `migrations/001_create_tables.sql`
4. Execute in SQL Editor

For **Local PostgreSQL**:
```bash
psql -U postgres -d affili_ai_db -f migrations/001_create_tables.sql
```

### 5. Run Backend

```bash
make run
# or: uvicorn app.main:app --reload
```

Server runs at `http://localhost:8000`

- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/health

### 6. Run Tests

```bash
make test
# or: pytest
```

### 7. Run Local Agent (Optional)

```bash
cd agent
python main.py
```

## API Endpoints

### Health Check

```
GET /api/health
```

### Programs API

```
GET    /api/v1/programs           - List all programs
POST   /api/v1/programs           - Create program
GET    /api/v1/programs/{id}      - Get program details
PUT    /api/v1/programs/{id}      - Update program
DELETE /api/v1/programs/{id}      - Delete program
```

### Applications API

```
GET    /api/v1/applications              - List applications
POST   /api/v1/applications              - Create application
GET    /api/v1/applications/{id}         - Get application
PUT    /api/v1/applications/{id}/status  - Update status
```

### Tasks API (Agent Queue)

```
GET    /api/v1/tasks                 - List tasks
POST   /api/v1/tasks                 - Create task
GET    /api/v1/tasks/{id}            - Get task details
POST   /api/v1/tasks/{id}/claim      - Claim task for agent
POST   /api/v1/tasks/{id}/update     - Update task progress
POST   /api/v1/tasks/poll            - Agent polls for work (requires Bearer token)
```

**Task States:**
PENDING, CLAIMED, RUNNING, PAUSED_FOR_CAPTCHA, RESUMED, SUBMITTED, COMPLETED, FAILED

### Response Pool API

```
GET    /api/v1/response-pool        - List Q&A pairs
POST   /api/v1/response-pool        - Add Q&A pair
GET    /api/v1/response-pool/{id}   - Get pair
PUT    /api/v1/response-pool/{id}   - Update pair
DELETE /api/v1/response-pool/{id}   - Delete pair
POST   /api/v1/response-pool/search - Search by similarity
```

## Connecting Frontend

Set environment variables in your Lovable frontend:

```javascript
VITE_API_BASE_URL=http://localhost:8000
```

Example API call:

```typescript
const response = await fetch(`${API_BASE_URL}/api/v1/programs`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    name: 'Test Program',
    affiliate_url: 'https://example.com',
    commission_rate: 0.1
  })
});
```

Update `ALLOWED_ORIGINS` in `.env` for CORS:
```
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173,https://yourfrontend.vercel.app
```

## Deployment

### Render/Railway/Heroku

1. Push repo to GitHub
2. Create project on Render/Railway/Heroku
3. Set environment variables from `.env`
4. Set run command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Deploy!

### Docker

```bash
docker build -t affili-ai-backend .
docker run -p 8000:8000 -e DATABASE_URL=postgresql://... affili-ai-backend
```

## Security

### Credential Encryption

All API keys are encrypted with AES-256-GCM:

```python
from app.core.security import encrypt_secret, decrypt_secret

encrypted = encrypt_secret("api_key_xyz")
plaintext = decrypt_secret(encrypted)
```

**MVP approach:**
- Static encryption key in .env
- Suitable for development and MVP

**Production approach (TODO):**
- Per-user key derivation
- Master key rotation
- KMS integration (AWS KMS, HashiCorp Vault)
- Zero-knowledge proof system

### JWT Tokens

- Short-lived access tokens (30 min default)
- Configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`

### Agent Authentication

- Bearer token authentication (MVP)
- Future: Per-agent API keys with rate limiting

## Vision & LLM Integration

### Current: Stub Adapter

MVP uses heuristic-based field detection. No external LLM calls.

### Future: Gemini Vision

```env
VISION_PROVIDER=gemini
GEMINI_API_KEY=your-key
```

### Future: OpenAI GPT-4 Vision

```env
VISION_PROVIDER=openai
OPENAI_API_KEY=your-key
```

Implementation hooks marked with `# TODO:` in `app/services/vision_adapter.py`.

## Testing

```bash
# Run all tests
pytest

# Run specific test
pytest tests/test_api.py::test_create_program

# Run with coverage
pytest --cov=app

# Run in verbose mode
pytest -v
```

See `tests/README.md` for detailed testing guide.

## Available Commands

```bash
make help           # Show all commands
make run            # Start dev server
make test           # Run tests
make test-cov       # Run tests with coverage
make lint           # Lint code
make format         # Format code
make migrations     # Show migration status
make agent          # Run local agent
make docker-build   # Build Docker image
```

## Project Structure

```
affili-ai-backend/
├── app/
│   ├── main.py                 # FastAPI application
│   ├── core/                   # Configuration, security, logging
│   ├── db/                     # Database session and base
│   ├── models/                 # SQLAlchemy ORM models
│   ├── schemas/                # Pydantic v2 schemas
│   ├── api/v1/                 # API endpoints
│   └── services/               # Business logic
├── agent/                      # Local Playwright agent
│   ├── main.py                # Agent entry point
│   ├── agent_config.env       # Agent configuration
│   └── Dockerfile             # Docker image for agent
├── migrations/                # Database migrations
├── tests/                     # Pytest tests
├── requirements.txt           # Python dependencies
├── Makefile                   # Development commands
├── Dockerfile                 # Backend Docker image
├── docker-compose.yml         # Local dev stack
├── .env.example              # Environment template
└── README.md                 # This file
```

## Development

### Code Style

- **Formatter**: Black
- **Linter**: Flake8
- **Type checking**: mypy

```bash
make format
make lint
```

### Adding Features

1. Create ORM model in `app/models/`
2. Create Pydantic schema in `app/schemas/`
3. Create service functions in `app/services/`
4. Create API routes in `app/api/v1/`
5. Write tests in `tests/`
6. Update migrations if adding database tables

### Environment Variables

```bash
cp .env.example .env
# Edit with your settings
```

## Troubleshooting

### ImportError: No module named 'app'

Ensure virtual environment is activated and you're in the `affili-ai-backend` directory.

### Database connection error

Check `DATABASE_URL` in `.env`:
- Supabase: `postgresql://[user]:[password]@[host]:[port]/[database]`
- Local: `postgresql://postgres:password@localhost:5432/affili_ai_db`
- SQLite: `sqlite:///./test.db`

### CORS error from frontend

Check `ALLOWED_ORIGINS` in `.env`. Should include your frontend URL (without trailing slash).

### Agent not connecting

1. Check `API_BASE_URL` in `agent/agent_config.env`
2. Verify backend is running: `curl http://localhost:8000/api/health`
3. Check `AGENT_API_KEY` matches backend config

## Migration Path

### Phase 1: MVP (Now)
- FastAPI monolith
- Local Playwright agents
- Task queue
- AES-256 credential encryption
- Stub vision/LLM integration

### Phase 2: Scaling
- Cloud-run agents (Google Cloud Run, AWS Lambda)
- Task broker (Redis, RabbitMQ)
- LLM/Vision APIs (Gemini, OpenAI)
- pgvector for semantic search

### Phase 3: Production
- Auth service (Supabase Auth, Auth0)
- Key rotation and zero-knowledge proofs
- Multi-tenant support
- Monitoring and observability

## License

MIT

---

**Built with**: FastAPI, SQLAlchemy, PostgreSQL, Playwright, Pydantic v2
