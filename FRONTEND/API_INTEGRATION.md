# Frontend Integration Guide

## ✅ Setup Complete

Your frontend is now configured to communicate with the FastAPI backend!

### Configuration Details

**Frontend Environment:**

- API Base URL: `http://localhost:8000/api`
- Framework: React + Vite
- Location: `D:\PROJECTS-REPOS\AFFILIATE-PROJ\affili-ai-hub\FRONTEND`

**Backend Status:**

- Running: `http://localhost:8000`
- API Docs: `http://localhost:8000/docs`
- CORS Enabled: ✓ (allows requests from frontend ports)

### How to Start Both

**Terminal 1 - Backend (already running):**

```bash
cd affili-ai-hub\affili-ai-backend
uvicorn app.main:app --reload
```

**Terminal 2 - Frontend:**

```bash
cd affili-ai-hub\FRONTEND
npm run dev
# or with bun:
bun run dev
```

Frontend will start on `http://localhost:8080` (check Vite output for actual port)

### Using the API Client

The frontend has a type-safe API client in `src/lib/api.ts`:

```typescript
import { api } from "@/lib/api";

// Get all programs
const programs = await api.getPrograms();

// Create application
const app = await api.createApplication(programId, responses);

// Get tasks
const tasks = await api.getTasks();

// Update task status
await api.updateTask(taskId, { status: "COMPLETED" });
```

### API Endpoints Available

All endpoints are prefixed with `/api/v1/`:

**Programs**

- `GET /programs` - List all programs
- `POST /programs` - Create program
- `GET /programs/{id}` - Get program details
- `PUT /programs/{id}` - Update program
- `DELETE /programs/{id}` - Delete program

**Applications**

- `GET /applications` - List applications (with optional `program_id` filter)
- `POST /applications` - Create application
- `GET /applications/{id}` - Get application
- `PUT /applications/{id}` - Update application
- `PATCH /applications/{id}/status` - Update status

**Tasks**

- `GET /tasks` - List tasks (with optional filters: `application_id`, `status`)
- `POST /tasks` - Create task
- `GET /tasks/{id}` - Get task
- `PUT /tasks/{id}` - Update task
- `PATCH /tasks/{id}/status` - Update status
- `POST /tasks/{id}/claim` - Claim task (agent)

**Credentials**

- `GET /credentials` - List credentials
- `POST /credentials` - Create credential
- `GET /credentials/{id}` - Get credential
- `PUT /credentials/{id}` - Update credential
- `DELETE /credentials/{id}` - Delete credential

**Response Pool**

- `GET /response-pool` - List responses (with optional `task_id` filter)
- `POST /response-pool` - Create response
- `GET /response-pool/{id}` - Get response
- `PUT /response-pool/{id}` - Update response
- `DELETE /response-pool/{id}` - Delete response

### Testing the Connection

**From Frontend (in browser console):**

```javascript
// Test health check
fetch("http://localhost:8000/api/v1/health")
  .then((r) => r.json())
  .then((d) => console.log(d));

// List programs
fetch("http://localhost:8000/api/v1/programs")
  .then((r) => r.json())
  .then((d) => console.log(d));
```

**From Backend Docs:**
Open `http://localhost:8000/docs` in browser to test all endpoints interactively

### Troubleshooting

**CORS Errors?**

- Check backend is running
- Verify `.env` has correct `ALLOWED_ORIGINS`
- Clear browser cache

**API Not responding?**

- Check backend terminal for errors
- Verify port 8000 is accessible
- Ensure firewall isn't blocking

**Async/Await Issues?**

- The API client fully supports async/await
- All functions return Promises
- Error handling via try/catch

### Next Steps

1. ✅ **Frontend Running** - Start with `npm run dev`
2. ⏳ **Create Sample Data** - Use `/docs` to add programs/applications
3. ⏳ **Build UI Components** - Connect components to `api.getPrograms()`, etc.
4. ⏳ **Agent Setup** - Docker container for task execution
5. ⏳ **Real Database** - Once network connectivity to Supabase is resolved

### Database Notes

- Currently using in-memory SQLite (dev mode)
- Tables will be created automatically on first request
- For production: switch `DATABASE_URL` to Supabase PostgreSQL
- Migration: `alembic upgrade head` (when Supabase connectivity works)

---

**Questions?** Check `src/lib/api.ts` for full type definitions and usage examples.
