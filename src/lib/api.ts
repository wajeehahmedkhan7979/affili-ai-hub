// API service - currently uses mock data, will be wired to Cursor backend
// Set VITE_API_BASE_URL environment variable to switch to real API

import { 
  mockPrograms, 
  mockApplications, 
  mockTasks, 
  mockResponsePool,
  mockActivityFeed,
  type Program,
  type Application,
  type Task,
  type ResponsePoolItem 
} from './mock-data';

const USE_MOCK = !import.meta.env.VITE_API_BASE_URL;
const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api/v1';

// Simulate network delay for realistic feel
const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

export const api = {
  // Programs
  async getPrograms(filters?: { status?: string; network?: string; search?: string }): Promise<Program[]> {
    if (USE_MOCK) {
      await delay(300);
      let programs = [...mockPrograms];
      if (filters?.status) {
        programs = programs.filter(p => p.status === filters.status);
      }
      if (filters?.network) {
        programs = programs.filter(p => p.network === filters.network);
      }
      if (filters?.search) {
        const search = filters.search.toLowerCase();
        programs = programs.filter(p => 
          p.name.toLowerCase().includes(search) || 
          p.description?.toLowerCase().includes(search)
        );
      }
      return programs;
    }
    const res = await fetch(`${API_BASE}/programs`);
    return res.json();
  },

  async getProgram(id: string): Promise<Program | undefined> {
    if (USE_MOCK) {
      await delay(200);
      return mockPrograms.find(p => p.id === id);
    }
    const res = await fetch(`${API_BASE}/programs/${id}`);
    return res.json();
  },

  // Applications
  async getApplications(): Promise<Application[]> {
    if (USE_MOCK) {
      await delay(300);
      return mockApplications;
    }
    const res = await fetch(`${API_BASE}/applications`);
    return res.json();
  },

  async createApplication(programId: string, responses: string[]): Promise<Application> {
    if (USE_MOCK) {
      await delay(500);
      const newApp: Application = {
        id: `app-${Date.now()}`,
        program_id: programId,
        status: 'PendingApproval',
        agent_status: 'WaitingForUserApproval',
        response_pool_used: responses,
        created_at: new Date().toISOString(),
      };
      return newApp;
    }
    const res = await fetch(`${API_BASE}/applications`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ program_id: programId, responses }),
    });
    return res.json();
  },

  // Tasks
  async getTasks(): Promise<Task[]> {
    if (USE_MOCK) {
      await delay(300);
      return mockTasks;
    }
    const res = await fetch(`${API_BASE}/tasks`);
    return res.json();
  },

  async updateTask(id: string, update: Partial<Task>): Promise<Task> {
    if (USE_MOCK) {
      await delay(300);
      const task = mockTasks.find(t => t.id === id);
      if (task) {
        Object.assign(task, update);
      }
      return task!;
    }
    const res = await fetch(`${API_BASE}/tasks/${id}/update`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(update),
    });
    return res.json();
  },

  // Response Pool
  async getResponsePool(query?: string): Promise<ResponsePoolItem[]> {
    if (USE_MOCK) {
      await delay(200);
      if (query) {
        return mockResponsePool.filter(r => 
          r.question_text.toLowerCase().includes(query.toLowerCase()) ||
          r.answer_text.toLowerCase().includes(query.toLowerCase())
        );
      }
      return mockResponsePool;
    }
    const res = await fetch(`${API_BASE}/response-pool/search${query ? `?q=${query}` : ''}`);
    return res.json();
  },

  // Activity Feed
  async getActivityFeed() {
    if (USE_MOCK) {
      await delay(200);
      return mockActivityFeed;
    }
    const res = await fetch(`${API_BASE}/activity`);
    return res.json();
  },

  // Dashboard Stats
  async getDashboardStats() {
    if (USE_MOCK) {
      await delay(200);
      return {
        programsFound: mockPrograms.length,
        pendingApprovals: mockApplications.filter(a => a.status === 'PendingApproval').length,
        applicationsSubmitted: mockApplications.length,
        connectedAgents: 1,
      };
    }
    const res = await fetch(`${API_BASE}/stats`);
    return res.json();
  },

  // Agent Status
  async getAgentStatus() {
    if (USE_MOCK) {
      await delay(100);
      return { connected: true, lastPing: new Date().toISOString() };
    }
    const res = await fetch(`${API_BASE}/agent/status`);
    return res.json();
  },
};
