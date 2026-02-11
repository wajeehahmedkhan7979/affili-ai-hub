// API service - Connected to FastAPI backend
// Set VITE_API_BASE_URL environment variable to connect to backend

import {
  mockPrograms,
  mockApplications,
  mockTasks,
  mockResponsePool,
  mockActivityFeed,
  type Program,
  type Application,
  type Task,
  type ResponsePoolItem,
} from "./mock-data";

const getUseMock = () => {
  const saved = localStorage.getItem('demoMode');
  const demoMode = saved !== null ? JSON.parse(saved) : false; // Default to false for real implementation
  return demoMode || !import.meta.env.VITE_API_BASE_URL;
};

const API_BASE = import.meta.env.VITE_API_BASE_URL || "/api/v1";

// Simulate network delay for realistic feel
const delay = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

// Helper function for API requests
async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {},
): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  
  // Get credentials from localStorage
  const token = localStorage.getItem('auth_token');
  const tenantId = localStorage.getItem('auth_tenant_id');
  
  const headers = {
    "Content-Type": "application/json",
    ...(token ? { "Authorization": `Bearer ${token}` } : {}),
    ...(tenantId ? { "X-Tenant-ID": tenantId } : { "X-Tenant-ID": "00000000-0000-0000-0000-000000000000" }),
    ...options.headers,
  };

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (!response.ok) {
    if (response.status === 401) {
      // Token expired or invalid, clear local storage and redirect to login
      localStorage.removeItem('auth_token');
      localStorage.removeItem('auth_user');
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
    }
    
    let errorDetail = response.statusText;
    try {
      const errorJson = await response.json();
      errorDetail = errorJson.detail || errorDetail;
    } catch {
      // Ignored
    }
    throw new Error(errorDetail);
  }

  return response.json() as Promise<T>;
}

export const api = {
  // Programs
  async getPrograms(filters?: {
    status?: string;
    network?: string;
    search?: string;
  }): Promise<Program[]> {
    if (getUseMock()) {
      await delay(300);
      let programs = [...mockPrograms];
      if (filters?.status) {
        programs = programs.filter((p) => p.status === filters.status);
      }
      if (filters?.network) {
        programs = programs.filter((p) => p.network === filters.network);
      }
      if (filters?.search) {
        const search = filters.search.toLowerCase();
        programs = programs.filter(
          (p) =>
            p.name.toLowerCase().includes(search) ||
            p.description?.toLowerCase().includes(search),
        );
      }
      return programs;
    }
    const res = await fetch(`${API_BASE}/programs`);
    const data = await res.json();
    const items = Array.isArray(data) ? data : [];
    
    // Map backend response to frontend Program interface
    return items.map((p: any) => ({
      ...p,
      // Frontend expects 'status' string, backend has 'is_active' bool
      status: p.status || (p.is_active ? "Discovered" : "Rejected"),
      // Frontend expects 'network', backend doesn't have it yet
      network: p.network || "Direct", 
      // Frontend expects 'commission', backend has 'commission_rate'
      commission: p.commission || (p.commission_rate ? `${p.commission_rate}%` : "N/A"),
      // Frontend expects 'url' for external link
      url: p.url || p.signup_url || p.affiliate_url || p.base_url || "#",
    }));
  },

  async getProgram(id: string): Promise<Program | undefined> {
    if (getUseMock()) {
      await delay(200);
      return mockPrograms.find((p) => p.id === id);
    }
    const res = await fetch(`${API_BASE}/programs/${id}`);
    return res.json();
  },

  async deleteProgram(id: string): Promise<void> {
    if (getUseMock()) {
      await delay(200);
      const index = mockPrograms.findIndex((p) => p.id === id);
      if (index > -1) {
        mockPrograms.splice(index, 1);
      }
      return;
    }
    const res = await fetch(`${API_BASE}/programs/${id}`, {
      method: 'DELETE',
      headers: {
        "Content-Type": "application/json",
        "X-User-Email": "dev@example.com",
        "X-Tenant-ID": "00000000-0000-0000-0000-000000000000",
      },
    });
    if (!res.ok) {
      const errorText = await res.text().catch(() => 'Unknown error');
      console.error('Delete failed:', res.status, errorText);
      throw new Error(`Failed to delete program: ${res.status} ${errorText}`);
    }
  },

  // Applications
  async getApplications(): Promise<Application[]> {
    if (getUseMock()) {
      await delay(300);
      return mockApplications;
    }
    const res = await fetch(`${API_BASE}/applications`);
    const data = await res.json();
    return Array.isArray(data) ? data : [];
  },

  async createApplication(
    programId: string,
    responses: string[],
  ): Promise<Application> {
    if (getUseMock()) {
      await delay(500);
      const newApp: Application = {
        id: `app-${Date.now()}`,
        program_id: programId,
        status: "PendingApproval",
        agent_status: "WaitingForUserApproval",
        response_pool_used: responses,
        created_at: new Date().toISOString(),
      };
      return newApp;
    }
    const res = await fetch(`${API_BASE}/applications`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ program_id: programId, responses }),
    });
    return res.json();
  },

  // Tasks
  async getTasks(): Promise<Task[]> {
    if (getUseMock()) {
      await delay(300);
      return mockTasks;
    }
    const res = await fetch(`${API_BASE}/tasks`);
    const data = await res.json();
    return Array.isArray(data) ? data : [];
  },

  async getTask(id: string): Promise<Task> {
    if (getUseMock()) {
      await delay(200);
      const task = mockTasks.find((t) => t.id === id);
      if (!task) throw new Error("Task not found");
      return task;
    }
    return apiRequest<Task>(`/tasks/${id}`);
  },

  async createTask(task: Partial<Task>): Promise<Task> {
    if (getUseMock()) {
        await delay(300);
        const newTask: Task = {
            id: `task-${Date.now()}`,
            task_type: task.task_type || "DISCOVER_PROGRAM",
            status: "PENDING",
            payload: task.payload || {},
            created_at: new Date().toISOString(),
            ...task
        } as Task;
        mockTasks.push(newTask);
        return newTask;
    }
    return apiRequest<Task>("/tasks", {
        method: "POST",
        body: JSON.stringify(task),
    });
  },

  async updateTask(id: string, update: Partial<Task>): Promise<Task> {
    if (getUseMock()) {
      await delay(300);
      const task = mockTasks.find((t) => t.id === id);
      if (task) {
        Object.assign(task, update);
      }
      return task!;
    }
    const res = await fetch(`${API_BASE}/tasks/${id}/update`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(update),
    });
    return res.json();
  },

  // Response Pool
  async getResponsePool(query?: string): Promise<ResponsePoolItem[]> {
    if (getUseMock()) {
      await delay(200);
      if (query) {
        return mockResponsePool.filter(
          (r) =>
            r.question_text.toLowerCase().includes(query.toLowerCase()) ||
            r.answer_text.toLowerCase().includes(query.toLowerCase()),
        );
      }
      return mockResponsePool;
    }
    
    try {
      const url = `${API_BASE}/response-pool`;
      // Note: Search endpoint in backend is POST /response-pool/search
      // But for the list view, we can just use the base endpoint and filter client-side if needed,
      // or implement the POST search here if a query is provided.
      
      let res;
      if (query) {
        res = await fetch(`${API_BASE}/response-pool/search`, {
          method: 'POST',
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ query, limit: 100 })
        });
      } else {
        res = await fetch(url);
      }
      
      const data = await res.json();
      const items = Array.isArray(data) ? data : [];
      
      return items.map((item: any) => ({
        id: item.id || `rp-${Math.random()}`,
        question_text: item.question || item.question_text || "",
        answer_text: item.answer || item.answer_text || "",
        context: Array.isArray(item.context) ? item.context : (item.category ? [item.category] : []),
        approval_rate: item.relevance_score || item.approval_rate || 0.9,
        last_used_date: item.updated_at || item.created_at || new Date().toISOString(),
      }));
    } catch (e) {
      console.error("Failed to fetch response pool:", e);
      return [];
    }
  },

  async createResponsePoolItem(item: Partial<ResponsePoolItem>): Promise<ResponsePoolItem> {
    if (getUseMock()) {
      await delay(300);
      const newItem: ResponsePoolItem = {
        id: `rp-${Date.now()}`,
        question_text: item.question_text || "",
        answer_text: item.answer_text || "",
        context: item.context || [],
        approval_rate: 1.0,
        last_used_date: new Date().toISOString(),
      };
      mockResponsePool.push(newItem);
      return newItem;
    }
    
    // Backend expects { question, answer, category, embedding }
    const res = await fetch(`${API_BASE}/response-pool`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        question: item.question_text,
        answer: item.answer_text,
        category: item.context && item.context.length > 0 ? item.context[0] : null
      }),
    });
    
    if (!res.ok) throw new Error("Failed to create response");
    const data = await res.json();
    return {
      id: data.id,
      question_text: data.question,
      answer_text: data.answer,
      context: data.category ? [data.category] : [],
      approval_rate: data.relevance_score || 0.9,
      last_used_date: data.updated_at || data.created_at,
    };
  },

  // Activity Feed
  async getActivityFeed() {
    if (getUseMock()) {
      await delay(200);
      return mockActivityFeed;
    }
    try {
      // Backend uses /audit for activity tracking
      const res = await fetch(`${API_BASE}/audit`);
      const data = await res.json();
      return Array.isArray(data) ? data : [];
    } catch (e) {
      console.error("Failed to fetch activity feed:", e);
      return [];
    }
  },

  // Dashboard Stats
  async getDashboardStats() {
    if (getUseMock()) {
      await delay(200);
      return {
        programsFound: mockPrograms.length,
        pendingApprovals: mockApplications.filter(
          (a) => a.status === "PendingApproval",
        ).length,
        applicationsSubmitted: mockApplications.length,
        connectedAgents: 1,
      };
    }
    try {
      // Backend uses /dashboards/system-overview for dashboard metrics
      const res = await fetch(`${API_BASE}/dashboards/system-overview`);
      return res.json();
    } catch (e) {
      console.error("Failed to fetch dashboard stats:", e);
      return {
        programsFound: 0,
        pendingApprovals: 0,
        applicationsSubmitted: 0,
        connectedAgents: 0,
      };
    }
  },

  // Agent Status
  async getAgentStatus() {
    if (getUseMock()) {
      await delay(100);
      return { connected: true, lastPing: new Date().toISOString() };
    }
    return apiRequest<{connected: boolean, lastPing: string | null}>("/agent/status");
  },

  // Governance & Status
  async getAiStatus(tenantId: string): Promise<{
    ai_enabled: boolean;
    status: string;
    reason?: string;
    disabled_at?: string;
  }> {
    if (getUseMock()) {
      await delay(100);
      return { ai_enabled: true, status: "OPERATIONAL" };
    }
    // Note: tenantId is sent in headers by apiRequest, but endpoint needs it in URL
    return apiRequest<any>(`/governance/tenant/${tenantId}/status`);
  },

  // Operator Actions
  async getPausedTasks(limit: number = 50): Promise<any> {
    if (getUseMock()) {
      await delay(200);
      return { tasks: mockTasks.filter(t => t.status.startsWith('PAUSED')) };
    }
    return apiRequest<any>(`/operator/tasks/paused?limit=${limit}`);
  },

  async resumeTask(taskId: string, reason?: string): Promise<any> {
    if (getUseMock()) {
      await delay(300);
      const task = mockTasks.find(t => t.id === taskId);
      if (task) task.status = 'PENDING';
      return { status: 'PENDING' };
    }
    return apiRequest<any>(`/operator/tasks/${taskId}/resume`, {
      method: 'POST',
      body: JSON.stringify({ reason })
    });
  },

  async cancelTask(taskId: string, reason: string): Promise<any> {
    if (getUseMock()) {
      await delay(300);
      const task = mockTasks.find(t => t.id === taskId);
      if (task) task.status = 'FAILED_OPERATOR_CANCEL';
      return { status: 'FAILED_OPERATOR_CANCEL' };
    }
    return apiRequest<any>(`/operator/tasks/${taskId}/cancel`, {
      method: 'POST',
      body: JSON.stringify({ reason })
    });
  },

  // Health
  async getHealth() {
    if (getUseMock()) {
      return { status: "ok", version: "1.0.0", time: new Date().toISOString(), environment: "production" };
    }
    return apiRequest<{status: string, version: string, time: string, environment: string}>("/health");
  },

  // SLA Metrics
  async getSlaMetrics(days: number = 7) {
    if (getUseMock()) {
      return {
        mttr_minutes: 12.5,
        captcha_rate: 0.05,
        human_intervention_rate: 0.08,
        total_tasks: 156
      };
    }
    return apiRequest<any>(`/dashboards/sla?days=${days}`);
  },

  // LLM Costs
  async getLlmCosts(days: number = 30) {
    if (getUseMock()) {
      return {
        total_cost_usd: 0.45,
        total_tokens: 12500,
        total_calls: 45
      };
    }
    return apiRequest<any>(`/governance/llm-costs?days=${days}`);
  },
};
