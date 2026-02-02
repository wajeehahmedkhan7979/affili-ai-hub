# AFFILI-AI Frontend - Setup & Integration Guide

## 🚀 Frontend Status: READY ✅

The React Vite frontend is fully configured and connected to the backend API.

---

## ⚡ Quick Start

### Start Both Services

**Option 1: PowerShell Background Jobs (RECOMMENDED)**

```powershell
# Start backend
$backendJob = Start-Job -ScriptBlock {
    cd "D:\PROJECTS-REPOS\AFFILIATE-PROJ\affili-ai-hub\affili-ai-backend"
    python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --log-level error
}

# Start frontend
$frontendJob = Start-Job -ScriptBlock {
    cd "D:\PROJECTS-REPOS\AFFILIATE-PROJ\affili-ai-hub\FRONTEND"
    npm run dev
}

Start-Sleep 4

# View jobs
Get-Job | Select-Object Id, State

# Open frontend (copy URL from console output)
```

**Option 2: Two Separate Terminals**

Terminal 1 - Backend:

```bash
cd affili-ai-backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Terminal 2 - Frontend:

```bash
cd FRONTEND
npm run dev
```

---

## 🌐 Access Points

| Service     | URL                         | Purpose              |
| ----------- | --------------------------- | -------------------- |
| Frontend    | http://127.0.0.1:5173       | React Vite app       |
| Backend API | http://127.0.0.1:8000/api   | REST API             |
| API Docs    | http://127.0.0.1:8000/docs  | Swagger UI           |
| ReDoc       | http://127.0.0.1:8000/redoc | Alternative API docs |

---

## 📊 Integration Test Results

```
============================================================
TESTING FRONTEND-BACKEND INTEGRATION
============================================================
Health Check         GET    200  ✓ OK
List Programs        GET    200  ✓ OK
Create Program       POST   201  ✓ OK
============================================================
```

All endpoints verified working with CORS enabled.

---

## 🏗️ Frontend Architecture

```
FRONTEND/
├── src/
│   ├── App.tsx                    # Main app with routing
│   ├── pages/                     # Page components
│   │   ├── Dashboard.tsx
│   │   ├── Programs.tsx
│   │   ├── Applications.tsx
│   │   ├── Tasks.tsx
│   │   ├── ResponsePool.tsx
│   │   ├── AgentSetup.tsx
│   │   ├── Integrations.tsx
│   │   ├── Settings.tsx
│   │   └── NotFound.tsx
│   ├── components/                # UI components (shadcn/ui)
│   ├── lib/
│   │   ├── api.ts                 # Type-safe API client
│   │   └── utils.ts               # Utility functions
│   ├── hooks/                     # Custom React hooks
│   ├── main.tsx                   # Entry point
│   └── index.css                  # Global styles
├── public/                        # Static assets
├── .env                           # Environment config
├── vite.config.ts                 # Vite configuration
├── tailwind.config.ts             # Tailwind CSS config
└── package.json                   # Dependencies & scripts
```

---

## 🔌 API Client Integration

The frontend uses a **type-safe API client** (`src/lib/api.ts`) that provides:

```typescript
// Programs
api.programs.list(); // GET /api/v1/programs
api.programs.create(data); // POST /api/v1/programs
api.programs.get(id); // GET /api/v1/programs/{id}
api.programs.update(id, data); // PUT /api/v1/programs/{id}
api.programs.delete(id); // DELETE /api/v1/programs/{id}

// Applications
api.applications.list();
api.applications.create(data);
api.applications.get(id);
api.applications.updateStatus(id, status);

// Tasks
api.tasks.list();
api.tasks.create(data);
api.tasks.claim(id, agentId);
api.tasks.updateStatus(id, data);

// Response Pool
api.responsePool.list();
api.responsePool.create(data);
api.responsePool.search(query);
```

---

## 📝 Available Routes

### Page Routes

- `/` - Dashboard
- `/programs` - Programs management
- `/applications` - Applications tracking
- `/tasks` - Task management
- `/response-pool` - Q&A responses
- `/agent` - Agent setup
- `/integrations` - Integration settings
- `/settings` - App settings

---

## 🎨 UI Framework

- **Vite 5.4.19** - Fast build tool and dev server
- **React 18** - UI library
- **TypeScript** - Type safety
- **Tailwind CSS** - Utility-first styling
- **shadcn/ui** - Component library (30+ components)
- **React Router** - Client-side routing
- **React Query** - Data fetching & caching
- **React Hook Form** - Form management

---

## 🔐 Environment Configuration

**.env file:**

```env
VITE_API_BASE_URL=http://localhost:8000/api
```

This configures the API endpoint for the frontend. During development, requests go to the local backend. For production, update this URL.

---

## 📦 NPM Commands

```bash
# Development
npm run dev              # Start dev server with hot reload

# Production
npm run build           # Build optimized bundle
npm run build:dev       # Build with dev flags
npm run preview         # Preview production build locally

# Quality
npm run lint            # Check code quality
npm run test            # Run tests once
npm run test:watch      # Run tests in watch mode
```

---

## 🔧 Development Workflow

1. **Start Services**

   ```powershell
   # Backend
   $job1 = Start-Job { cd affili-ai-backend; python -m uvicorn ... }

   # Frontend
   $job2 = Start-Job { cd FRONTEND; npm run dev }
   ```

2. **Make Changes**
   - Edit components, pages, or API client
   - Vite hot-reloads automatically
   - TypeScript catches errors immediately

3. **Test API Integration**
   - Open http://127.0.0.1:5173
   - Test CRUD operations
   - Check console for errors
   - Use browser DevTools Network tab to inspect requests

4. **View API Docs**
   - Open http://127.0.0.1:8000/docs
   - Try endpoints directly
   - View request/response schemas

---

## 🚀 Deployment Ready

### Frontend (Vercel)

```bash
# Build
npm run build

# Deploy to Vercel
vercel --prod
```

Update `VITE_API_BASE_URL` to production backend URL.

### Backend (Render)

```bash
# Deploy from GitHub
# Set environment variables:
# - DATABASE_URL → Supabase PostgreSQL
# - SECRET_KEY → Production secret
# - ALGORITHM → ES256
```

---

## 📱 Features Implemented

✅ **Dashboard** - Overview and statistics  
✅ **Programs Management** - Full CRUD for affiliate programs  
✅ **Applications Tracking** - Manage program applications  
✅ **Task Management** - Queue and assign tasks to agents  
✅ **Response Pool** - Store and search Q&A responses  
✅ **Settings** - Configure app preferences  
✅ **API Integration** - Type-safe backend communication  
✅ **Error Handling** - User-friendly error messages  
✅ **Form Validation** - Client-side validation with React Hook Form  
✅ **Responsive Design** - Works on desktop and mobile

---

## 🔍 Testing

### Manual Testing Checklist

- [ ] Frontend loads without errors
- [ ] Navigate between all pages
- [ ] Create a program via form
- [ ] View created program in list
- [ ] Update program information
- [ ] Delete a program
- [ ] Check API calls in DevTools Network tab
- [ ] Verify CORS headers are present
- [ ] Test on mobile/tablet viewport
- [ ] Check console for any JavaScript errors

### API Integration Tests

```python
# Run test_api_comprehensive.py
python d:\PROJECTS-REPOS\AFFILIATE-PROJ\affili-ai-hub\affili-ai-backend\test_api_comprehensive.py
```

---

## 🐛 Troubleshooting

### "Cannot GET /api/v1/programs"

- ✅ Backend is running on port 8000
- ✅ CORS is enabled in backend
- ✅ `VITE_API_BASE_URL` is correct in .env

### "Proxy error"

- Check that backend is responding:
  ```bash
  curl http://127.0.0.1:8000/api/health
  ```
- Verify port 8000 is not in use

### Vite dev server not starting

```bash
cd FRONTEND
npm install
npm run dev
```

### Hot reload not working

- Restart dev server: `Ctrl+C` then `npm run dev`
- Check for TypeScript errors

---

## 📚 Next Steps

1. **Review Pages**
   - Check each page component in `src/pages/`
   - Understand the layout and data flow

2. **Customize UI**
   - Update brand colors in `tailwind.config.ts`
   - Modify component styles
   - Add custom themes

3. **Extend Features**
   - Add new pages
   - Implement new API endpoints
   - Add authentication/authorization

4. **Optimize Performance**
   - Lazy load routes
   - Optimize images
   - Profile bundle size

5. **Deploy**
   - Build and deploy frontend
   - Configure production API URL
   - Set up monitoring

---

**Status:** Frontend Ready for Development & Testing ✅  
**Last Updated:** January 28, 2026  
**Next Phase:** Full-stack feature development
