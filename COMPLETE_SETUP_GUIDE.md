# AFFILI-AI Full Stack - Complete Setup & Getting Started Guide

## 📋 Project Overview

**AFFILI-AI Hub** is a full-stack application for managing affiliate marketing programs with AI-powered automation.

- **Backend:** FastAPI (Python) - REST API with database
- **Frontend:** React Vite (TypeScript) - Modern web interface
- **Database:** SQLite (dev) / PostgreSQL (prod)
- **Status:** ✅ **FULLY OPERATIONAL**

---

## 🚀 Quick Start (5 Minutes)

### Prerequisites

- Python 3.13.5+ installed
- Node.js 18+ and npm installed
- Backend dependencies installed
- Frontend dependencies installed

### Run Everything

**PowerShell:**

```powershell
# Start backend in background
$backendJob = Start-Job -ScriptBlock {
    cd "D:\PROJECTS-REPOS\AFFILIATE-PROJ\affili-ai-hub\affili-ai-backend"
    python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --log-level error
}

# Start frontend in background
$frontendJob = Start-Job -ScriptBlock {
    cd "D:\PROJECTS-REPOS\AFFILIATE-PROJ\affili-ai-hub\FRONTEND"
    npm run dev
}

Start-Sleep 5

# Done! Copy the frontend URL from console and open in browser
Write-Host "✓ Backend: http://127.0.0.1:8000"
Write-Host "✓ Frontend: http://127.0.0.1:5173 (or shown in console)"
Write-Host "✓ API Docs: http://127.0.0.1:8000/docs"
```

**Bash/Terminal:**

```bash
# Terminal 1 - Backend
cd affili-ai-backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

# Terminal 2 - Frontend
cd FRONTEND
npm run dev
```

---

## 📍 Access Points

| Service            | URL                         | Purpose              |
| ------------------ | --------------------------- | -------------------- |
| Frontend App       | http://172.19.176.1:8080/   | Web interface        |
| Backend API        | http://127.0.0.1:8000       | REST API server      |
| API Docs (Swagger) | http://127.0.0.1:8000/docs  | Interactive API docs |
| ReDoc              | http://127.0.0.1:8000/redoc | Alternative API docs |

---

## 📁 Project Structure

```
affili-ai-hub/
├── affili-ai-backend/              # FastAPI backend
│   ├── app/
│   │   ├── main.py                # App entry point
│   │   ├── core/                  # Configuration
│   │   ├── db/                    # Database layer
│   │   ├── models/                # SQLAlchemy models (5 models)
│   │   ├── schemas/               # Pydantic schemas
│   │   └── api/v1/                # API endpoints
│   ├── alembic/                   # Database migrations
│   ├── .env                       # Backend config
│   ├── requirements.txt           # Python dependencies
│   ├── BACKEND_STATUS.md          # Backend documentation
│   └── affili_ai.db              # SQLite database
│
├── FRONTEND/                       # React Vite frontend
│   ├── src/
│   │   ├── pages/                 # Page components
│   │   ├── components/            # UI components
│   │   ├── lib/                   # API client & utils
│   │   ├── hooks/                 # Custom hooks
│   │   ├── App.tsx                # Main app
│   │   └── main.tsx               # Entry point
│   ├── public/                    # Static assets
│   ├── .env                       # Frontend config
│   ├── package.json               # Dependencies
│   ├── vite.config.ts             # Vite config
│   ├── FRONTEND_SETUP.md          # Frontend documentation
│   └── API_INTEGRATION.md         # API integration guide
│
└── README.md                       # Project documentation
```

---

## 🔧 Technology Stack

### Backend

| Technology | Version | Purpose         |
| ---------- | ------- | --------------- |
| Python     | 3.13.5  | Runtime         |
| FastAPI    | 0.104.1 | Web framework   |
| SQLAlchemy | 2.1.10  | ORM             |
| Uvicorn    | 0.30.0+ | ASGI server     |
| Pydantic   | 2.5.0   | Data validation |
| Alembic    | 1.14.0  | Migrations      |

### Frontend

| Technology   | Version | Purpose           |
| ------------ | ------- | ----------------- |
| React        | 18.3.1  | UI library        |
| Vite         | 5.4.19  | Build tool        |
| TypeScript   | 5.6.3   | Type safety       |
| Tailwind CSS | 3.4.1   | Styling           |
| shadcn/ui    | Latest  | Component library |
| React Router | 6.31.1  | Routing           |
| React Query  | 5.83.0  | Data fetching     |

### Database

| Environment | Database              | Status     |
| ----------- | --------------------- | ---------- |
| Development | SQLite                | ✅ Working |
| Production  | PostgreSQL (Supabase) | 🔧 Ready   |

---

## 📊 API Endpoints

### Health & Status

```
GET  /api/health                    # Health check
```

### Programs (Affiliate Programs)

```
GET    /api/v1/programs             # List all programs
POST   /api/v1/programs             # Create new program
GET    /api/v1/programs/{id}        # Get specific program
PUT    /api/v1/programs/{id}        # Update program
DELETE /api/v1/programs/{id}        # Delete program
```

### Applications

```
GET    /api/v1/applications         # List applications
POST   /api/v1/applications         # Create application
GET    /api/v1/applications/{id}    # Get application
PUT    /api/v1/applications/{id}/status  # Update status
```

### Tasks

```
GET    /api/v1/tasks                # List tasks
POST   /api/v1/tasks                # Create task
GET    /api/v1/tasks/{id}           # Get task
POST   /api/v1/tasks/{id}/claim     # Agent claims task
POST   /api/v1/tasks/{id}/update    # Update task status
POST   /api/v1/tasks/poll           # Poll for tasks
```

### Response Pool (Q&A)

```
GET    /api/v1/response-pool        # List responses
POST   /api/v1/response-pool        # Create response
GET    /api/v1/response-pool/{id}   # Get response
PUT    /api/v1/response-pool/{id}   # Update response
DELETE /api/v1/response-pool/{id}   # Delete response
POST   /api/v1/response-pool/search # Search responses
```

---

## 🗄️ Database Models

### Program

```python
id: UUID (primary key)
name: str
affiliate_url: str
commission_rate: float
description: Optional[str]
is_active: bool
created_at: datetime
updated_at: datetime
```

### Application

```python
id: UUID
program_id: UUID (FK)
status: str (pending, approved, rejected)
applied_date: datetime
updated_date: datetime
notes: Optional[str]
```

### Task

```python
id: UUID
name: str
agent_id: Optional[UUID]
status: str (pending, in_progress, completed, failed)
created_at: datetime
updated_at: datetime
scheduled_for: Optional[datetime]
```

### Credential

```python
id: UUID
name: str
api_key: str (encrypted)
provider: str
created_at: datetime
```

### ResponsePool

```python
id: UUID
question: str
answer: str
embeddings: List[float]
tags: List[str]
created_at: datetime
```

---

## ⚙️ Configuration

### Backend (.env)

```env
# Database
DATABASE_URL="sqlite:///./affili_ai.db"

# API
API_BASE_URL=http://localhost:8000
DEBUG=True

# JWT
SECRET_KEY=your-secret-key
ALGORITHM=ES256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS (Frontend URLs)
ALLOWED_ORIGINS=["http://localhost:3000", "http://localhost:5173"]

# Storage
STORAGE_PROVIDER=local
LOCAL_STORAGE_PATH=./uploads
```

### Frontend (.env)

```env
VITE_API_BASE_URL=http://localhost:8000/api
```

---

## 🧪 Testing

### Backend API Tests

```bash
cd affili-ai-backend

# Run comprehensive API tests
python test_api_comprehensive.py
```

### Frontend Development

```bash
cd FRONTEND

# Run tests
npm run test

# Watch mode
npm run test:watch

# Build for production
npm run build
```

---

## 📈 Full Stack Workflow

1. **Start Services**

   ```powershell
   # Backend in job 1
   # Frontend in job 2
   ```

2. **Open Frontend**
   - Go to http://127.0.0.1:5173
   - Navigate pages
   - Create/read/update/delete programs

3. **Monitor Requests**
   - Open DevTools (F12)
   - Go to Network tab
   - Observe API calls to backend

4. **Check API Docs**
   - Go to http://127.0.0.1:8000/docs
   - Test endpoints directly
   - See request/response schemas

5. **View Logs**
   - Backend logs in terminal 1
   - Frontend logs in terminal 2

---

## 🔄 Development Cycle

```
Edit Code → Hot Reload → Test → Debug → Repeat
```

### Backend Changes

- Edit Python files
- Changes require server restart (Uvicorn reload if enabled)
- Or restart the Python process

### Frontend Changes

- Edit React/TypeScript files
- Automatic hot reload via Vite
- Browser reflects changes immediately
- TypeScript errors shown in console

---

## 🚀 Deployment

### Frontend (Vercel)

1. Build: `npm run build`
2. Deploy: `vercel --prod`
3. Set env: `VITE_API_BASE_URL=https://api.yourdomain.com`

### Backend (Render/Fly.io/AWS)

1. Set `DATABASE_URL` to production PostgreSQL
2. Set `SECRET_KEY` to production secret
3. Deploy from GitHub: `git push`

---

## 🔐 Authentication & Security

The platform follows a secure Multi-Tenant JWT-based architecture:

### Default Admin Credentials (E2E Verified)

- **Tenant ID**: `00000000-0000-0000-0000-000000000000`
- **Email**: `admin@example.com`
- **Password**: `password` (seeded in backend)

### RBAC Roles

| Role            | Access Level    | Description                                                      |
| --------------- | --------------- | ---------------------------------------------------------------- |
| **OWNER/ADMIN** | Full Access     | Can manage users, view all metrics, and use the LLM kill-switch. |
| **OPERATOR**    | Task Operations | Can claim and execute tasks, provide human feedback.             |
| **VIEWER**      | Read-Only       | Restricted to dashboards and task viewing.                       |

---

## 🛠️ Infrastructure Maintenance

### Critical Fixes Applied (Production Readiness)

1. **Password Hashing**: Downgraded `bcrypt` to `3.2.0` to ensure `passlib` compatibility on modern Python runtimes (3.12+).
2. **Operational Tables**: The following tables are now initialized for governance and auditing:
   - `llm_usage_log`: AI cost and token tracking ledger.
   - `tenant_runtime_flags`: Emergency AI kill-switch persistence.
   - `operator_action_log`: Transparent human intervention audit trail.

### Manual Table Creation

If operational tables are missing, run the following in the backend container/root:

```bash
python scripts/create_operational_tables.py
```

---

---

## 📊 Governance & Observability

### Dashboard Widgets (Integrated)

- **Operator Dashboard**: Live at `/dashboard` (after login).
    - **Worker Status**: Real-time active workers & queue depth.
    - **Governance Controls**: System Kill-Switch & Backup Triggers.
    - **Task Inspector**: Deep dive into individual task execution.
- **System Health**: Real-time status from `/api/v1/health`.
- **SLA Metrics**: MTTR (Mean Time to Resolution) and Human Intervention rates.
- **AI Cost Control**: Monthly token/USD consumption tracking.

### Verification Suite

Run the full suite of verification scripts to certify the environment:

```bash
# From affili-ai-backend root

# 1. E2E System Check
python scripts/verify_full_system.py

# 2. Chaos & Resilience Tests (Database/Worker Failures)
pytest tests/chaos/test_integrity_under_fire.py

# 3. Load & Scale Validation (200 Concurrent Tasks)
python scripts/load_test.py
```

---

## 🚀 Deployment Notes

- **PostgreSQL**: Production ready with `pgvector` for RAG.
- **Frontend**: Vite-built React app with `AuthContext` persistence.
- **API Base**: Managed via `.env` (`VITE_API_BASE_URL` and `API_BASE_URL`).

---

## 📚 Documentation Files

- **Backend**
  - [`affili-ai-backend/BACKEND_STATUS.md`](./affili-ai-backend/BACKEND_STATUS.md) - Backend setup & status
  - [`affili-ai-backend/API_INTEGRATION.md`](./affili-ai-backend/API_INTEGRATION.md) - Backend API details

- **Frontend**
  - [`FRONTEND/FRONTEND_SETUP.md`](./FRONTEND/FRONTEND_SETUP.md) - Frontend setup & dev guide
  - [`FRONTEND/API_INTEGRATION.md`](./FRONTEND/API_INTEGRATION.md) - Frontend API integration

---

## ✅ Verification Checklist

- [x] Backend FastAPI app created
- [x] 5 database models implemented
- [x] All CRUD endpoints working
- [x] SQLite database operational
- [x] Frontend React Vite app created
- [x] Type-safe API client implemented
- [x] CORS enabled for frontend
- [x] All pages/routes defined
- [x] Backend & frontend integrated
- [x] Full stack tested together

---

## 🐛 Common Issues & Solutions

### Backend won't start

```bash
# Check Python version
python --version  # Should be 3.13.5+

# Check dependencies
pip list | grep -E "fastapi|sqlalchemy|uvicorn"

# Reinstall if needed
pip install -r requirements.txt
```

### Frontend won't start

```bash
# Check Node version
node --version  # Should be 18+

# Reinstall dependencies
rm -rf node_modules package-lock.json
npm install

# Clear Vite cache
rm -rf .vite
npm run dev
```

### Can't connect to API

- Check backend is running on port 8000
- Check CORS is enabled in backend
- Check VITE_API_BASE_URL in frontend .env
- Use DevTools to see actual API requests

### Database locked

- Delete `affili_ai.db` to reset
- Close any other connections
- Restart backend

---

## 🎯 Next Steps

1. **Review Code**
   - Read backend models and routes
   - Review frontend pages and components
   - Understand API integration

2. **Customize**
   - Update branding/colors
   - Modify pages to match requirements
   - Add new features

3. **Test Thoroughly**
   - Manual testing of all CRUD operations
   - API integration testing
   - Performance testing

4. **Deploy**
   - Set up production database (PostgreSQL)
   - Deploy backend to Render/Fly.io
   - Deploy frontend to Vercel
   - Configure domain/DNS

---

## 📞 Support Resources

- FastAPI Docs: https://fastapi.tiangolo.com/
- React Docs: https://react.dev/
- Vite Docs: https://vitejs.dev/
- SQLAlchemy Docs: https://docs.sqlalchemy.org/
- Tailwind CSS: https://tailwindcss.com/

---

**Project Status:** ✅ **FULLY INTEGRATED & VERIFIED**  
**Last Updated:** February 9, 2026  
**Ready For:** Production Pilot & AI Automation

---

## 🚀 Pilot Operations

For the 30-day production pilot (v1.1), please adhere to the following:

- **Operations Strategy**: [PILOT_OPERATIONS_STRATEGY.md](file:///d:/PROJECTS-REPOS/AFFILIATE-PROJ/affili-ai-hub/PILOT_OPERATIONS_STRATEGY.md)
- **Pilot Checklist**: [PILOT_CHECKLIST.md](file:///d:/PROJECTS-REPOS/AFFILIATE-PROJ/affili-ai-hub/PILOT_CHECKLIST.md)
- **Post-Handoff Status**: ✅ **OPERATIONS MODE ACTIVE**

```

```
