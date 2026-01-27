# Frontend Integration Guide

This guide shows how to connect your Lovable frontend to the AFFILI-AI backend.

## Quick Integration

### 1. Environment Configuration

Add to your `.env.local` (Lovable/frontend):

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_API_VERSION=v1
```

For production:
```env
VITE_API_BASE_URL=https://api.youromain.com
VITE_API_VERSION=v1
```

### 2. API Client Helper

Create `src/lib/api-client.ts`:

```typescript
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const API_VERSION = import.meta.env.VITE_API_VERSION || 'v1';

export const apiClient = {
  async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const url = `${API_BASE_URL}/api/${API_VERSION}${endpoint}`;
    
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
      ...options,
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }

    return response.json();
  },

  // Programs
  getPrograms() {
    return this.request('/programs');
  },

  createProgram(data: any) {
    return this.request('/programs', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  updateProgram(id: string, data: any) {
    return this.request(`/programs/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },

  deleteProgram(id: string) {
    return this.request(`/programs/${id}`, {
      method: 'DELETE',
    });
  },

  // Applications
  createApplication(data: any) {
    return this.request('/applications', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  getApplications() {
    return this.request('/applications');
  },

  updateApplicationStatus(id: string, status: string) {
    return this.request(`/applications/${id}/status`, {
      method: 'PUT',
      body: JSON.stringify({ status }),
    });
  },

  // Tasks
  getTasks(status?: string) {
    const query = status ? `?status=${status}` : '';
    return this.request(`/tasks${query}`);
  },

  createTask(data: any) {
    return this.request('/tasks', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  getTask(id: string) {
    return this.request(`/tasks/${id}`);
  },

  updateTask(id: string, data: any) {
    return this.request(`/tasks/${id}/update`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  // Response Pool
  searchResponsePool(query: string, limit = 10) {
    return this.request('/response-pool/search', {
      method: 'POST',
      body: JSON.stringify({ query, limit, threshold: 0.0 }),
    });
  },

  createResponse(data: any) {
    return this.request('/response-pool', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },
};

export default apiClient;
```

### 3. Example: Programs Page Component

```typescript
import { useState, useEffect } from 'react';
import apiClient from '@/lib/api-client';

export function ProgramsPage() {
  const [programs, setPrograms] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadPrograms();
  }, []);

  async function loadPrograms() {
    try {
      const data = await apiClient.getPrograms();
      setPrograms(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load programs');
    } finally {
      setLoading(false);
    }
  }

  async function handleCreateProgram(formData: any) {
    try {
      await apiClient.createProgram(formData);
      await loadPrograms();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create program');
    }
  }

  if (loading) return <div>Loading...</div>;
  if (error) return <div className="error">{error}</div>;

  return (
    <div>
      <h1>Affiliate Programs</h1>
      
      <div className="program-list">
        {programs.map((program: any) => (
          <div key={program.id} className="program-card">
            <h3>{program.name}</h3>
            <p>Commission: {(program.commission_rate * 100).toFixed(1)}%</p>
            <a href={program.affiliate_url} target="_blank" rel="noopener noreferrer">
              Visit Program
            </a>
          </div>
        ))}
      </div>

      <div className="create-program-form">
        <h2>Add New Program</h2>
        <form onSubmit={(e) => {
          e.preventDefault();
          const formData = new FormData(e.currentTarget);
          handleCreateProgram({
            name: formData.get('name'),
            affiliate_url: formData.get('url'),
            commission_rate: parseFloat(formData.get('commission') as string),
            description: formData.get('description'),
            is_active: true,
          });
        }}>
          <input name="name" placeholder="Program Name" required />
          <input name="url" placeholder="Affiliate URL" required />
          <input name="commission" placeholder="Commission Rate" type="number" step="0.01" />
          <textarea name="description" placeholder="Description"></textarea>
          <button type="submit">Add Program</button>
        </form>
      </div>
    </div>
  );
}
```

### 4. Example: Applications Page Component

```typescript
import { useState, useEffect } from 'react';
import apiClient from '@/lib/api-client';

export function ApplicationsPage() {
  const [applications, setApplications] = useState([]);
  const [programs, setPrograms] = useState([]);

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    try {
      const [apps, progs] = await Promise.all([
        apiClient.getApplications(),
        apiClient.getPrograms(),
      ]);
      setApplications(apps);
      setPrograms(progs);
    } catch (err) {
      console.error('Failed to load data:', err);
    }
  }

  async function handleApplyToProgram(programId: string, userEmail: string) {
    try {
      const data = {
        program_id: programId,
        user_email: userEmail,
        user_data: JSON.stringify({ timestamp: new Date().toISOString() }),
      };
      await apiClient.createApplication(data);
      alert('Application submitted! Agent will process it shortly.');
      await loadData();
    } catch (err) {
      alert('Failed to submit application: ' + (err instanceof Error ? err.message : 'Unknown error'));
    }
  }

  return (
    <div>
      <h1>My Applications</h1>
      
      <div className="applications-list">
        {applications.map((app: any) => (
          <div key={app.id} className="application-card">
            <h3>{app.user_email}</h3>
            <p>Status: <strong>{app.status}</strong></p>
            <p>Applied: {new Date(app.created_at).toLocaleDateString()}</p>
          </div>
        ))}
      </div>

      <h2>Apply to Programs</h2>
      <div className="programs-grid">
        {programs.filter((p: any) => p.is_active).map((program: any) => (
          <div key={program.id} className="program-box">
            <h3>{program.name}</h3>
            <p>Commission: {(program.commission_rate * 100).toFixed(1)}%</p>
            <button onClick={() => {
              const email = prompt('Enter your email:');
              if (email) {
                handleApplyToProgram(program.id, email);
              }
            }}>
              Apply to Program
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
```

### 5. Example: Task Monitoring Component

```typescript
import { useState, useEffect } from 'react';
import apiClient from '@/lib/api-client';

export function TaskMonitorComponent() {
  const [tasks, setTasks] = useState<any[]>([]);
  const [refreshInterval, setRefreshInterval] = useState<NodeJS.Timeout | null>(null);

  useEffect(() => {
    loadTasks();
    
    // Refresh every 5 seconds
    const interval = setInterval(loadTasks, 5000);
    setRefreshInterval(interval);

    return () => clearInterval(interval);
  }, []);

  async function loadTasks() {
    try {
      const data = await apiClient.getTasks();
      setTasks(data);
    } catch (err) {
      console.error('Failed to load tasks:', err);
    }
  }

  const statusColors: Record<string, string> = {
    PENDING: 'yellow',
    CLAIMED: 'blue',
    RUNNING: 'cyan',
    COMPLETED: 'green',
    FAILED: 'red',
    PAUSED_FOR_CAPTCHA: 'orange',
  };

  return (
    <div>
      <h2>Agent Tasks</h2>
      <p>Last updated: {new Date().toLocaleTimeString()}</p>

      <div className="tasks-grid">
        {tasks.map((task: any) => (
          <div key={task.id} className={`task-card status-${statusColors[task.status]}`}>
            <div className="task-header">
              <h4>{task.task_type}</h4>
              <span className="status-badge">{task.status}</span>
            </div>
            
            <div className="task-details">
              <p>Agent: {task.agent_id || 'Unassigned'}</p>
              <p>Retries: {task.retry_count}/{task.max_retries}</p>
              <p>Created: {new Date(task.created_at).toLocaleTimeString()}</p>
            </div>

            {task.screenshot_url && (
              <a href={task.screenshot_url} target="_blank" rel="noopener noreferrer">
                View Screenshot
              </a>
            )}

            {task.error_message && (
              <p className="error-text">{task.error_message}</p>
            )}

            {task.logs && (
              <details>
                <summary>View Logs</summary>
                <pre>{task.logs}</pre>
              </details>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
```

## CORS Configuration

The backend is configured for CORS from your frontend URL. Update in `affili-ai-backend/.env`:

```env
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173,https://yourfrontend.vercel.app
```

## Error Handling

Always wrap API calls in try-catch:

```typescript
try {
  const programs = await apiClient.getPrograms();
} catch (error) {
  if (error instanceof Error) {
    console.error('API Error:', error.message);
    // Show user-friendly error message
  }
}
```

## Authentication (Future)

Once Supabase Auth is integrated:

```typescript
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(SUPABASE_URL, SUPABASE_KEY);

export async function authenticatedRequest(endpoint: string) {
  const { data: { session } } = await supabase.auth.getSession();
  
  return apiClient.request(endpoint, {
    headers: {
      Authorization: `Bearer ${session?.access_token}`,
    },
  });
}
```

## Testing API Locally

Use curl or Postman:

```bash
# Create a program
curl -X POST http://localhost:8000/api/v1/programs \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Program",
    "affiliate_url": "https://example.com",
    "commission_rate": 0.15
  }'

# List programs
curl http://localhost:8000/api/v1/programs

# Health check
curl http://localhost:8000/api/health
```

## Deployment to Vercel

1. Set environment variable in Vercel dashboard:
   ```
   VITE_API_BASE_URL=https://your-backend-url.com
   ```

2. Ensure backend CORS includes your Vercel domain

3. Deploy frontend normally

## Troubleshooting

### CORS Errors

If you see "Access to XMLHttpRequest blocked by CORS policy":
1. Check `ALLOWED_ORIGINS` in backend `.env`
2. Ensure frontend URL is listed (without trailing slash)
3. Restart backend server

### API Connection Issues

1. Verify backend is running: `curl http://localhost:8000/api/health`
2. Check frontend is pointing to correct `VITE_API_BASE_URL`
3. Look for network errors in browser DevTools
4. Check backend logs for error details

### TypeScript Types

Create `src/types/api.ts` for type safety:

```typescript
export interface Program {
  id: string;
  name: string;
  affiliate_url: string;
  commission_rate: number;
  description?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Application {
  id: string;
  program_id: string;
  user_email: string;
  status: 'PENDING' | 'IN_PROGRESS' | 'APPROVED' | 'REJECTED' | 'COMPLETED';
  created_at: string;
}

export interface Task {
  id: string;
  task_type: string;
  status: string;
  payload?: Record<string, any>;
  result?: Record<string, any>;
  agent_id?: string;
  created_at: string;
}
```

---

For more details, see [README.md](./README.md) in the backend directory.
