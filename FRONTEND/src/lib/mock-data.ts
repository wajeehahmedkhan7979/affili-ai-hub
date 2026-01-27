// Mock data matching Cursor API contracts

export interface Program {
  id: string;
  name: string;
  network: string;
  url: string;
  status: 'Discovered' | 'Applied' | 'Approved' | 'Rejected';
  created_at: string;
  last_action: string;
  logo?: string;
  description?: string;
  commission?: string;
}

export interface Application {
  id: string;
  program_id: string;
  status: 'PendingApproval' | 'Submitted' | 'Approved' | 'Rejected';
  agent_status: 'WaitingForUserApproval' | 'Processing' | 'Completed' | 'Failed';
  response_pool_used: string[];
  created_at: string;
  program?: Program;
}

export interface Task {
  id: string;
  type: 'APPLY_PROGRAM' | 'DISCOVER_PROGRAMS' | 'PUBLISH_CONTENT';
  payload: Record<string, string>;
  status: 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED' | 'PAUSED_FOR_CAPTCHA';
  created_at: string;
  logs: string[];
}

export interface ResponsePoolItem {
  id: string;
  question_text: string;
  answer_text: string;
  context: string[];
  approval_rate: number;
  last_used_date: string;
}

export const mockPrograms: Program[] = [
  {
    id: 'prog-001',
    name: 'AI Video Editor Pro',
    network: 'ClickBank',
    url: 'https://aivideoeditor.com/affiliate',
    status: 'Discovered',
    created_at: '2026-01-20T12:00:00Z',
    last_action: 'Discovery',
    description: 'Revolutionary AI-powered video editing software with 50% commission.',
    commission: '50%',
  },
  {
    id: 'prog-002',
    name: 'CryptoTrader AI',
    network: 'ShareASale',
    url: 'https://cryptotraderai.com/partners',
    status: 'Applied',
    created_at: '2026-01-19T10:30:00Z',
    last_action: 'Application Submitted',
    description: 'Automated crypto trading bot with machine learning algorithms.',
    commission: '30%',
  },
  {
    id: 'prog-003',
    name: 'FitnessPro 360',
    network: 'CJ Affiliate',
    url: 'https://fitnesspro360.com/affiliates',
    status: 'Approved',
    created_at: '2026-01-18T08:15:00Z',
    last_action: 'Approved',
    description: 'Complete fitness and nutrition tracking platform.',
    commission: '25%',
  },
  {
    id: 'prog-004',
    name: 'SmartHome Hub',
    network: 'ClickBank',
    url: 'https://smarthomehub.io/affiliate',
    status: 'Discovered',
    created_at: '2026-01-21T14:00:00Z',
    last_action: 'Discovery',
    description: 'IoT home automation platform with recurring commissions.',
    commission: '40%',
  },
  {
    id: 'prog-005',
    name: 'LearnCode Academy',
    network: 'Impact',
    url: 'https://learncodeacademy.com/partners',
    status: 'Rejected',
    created_at: '2026-01-17T09:00:00Z',
    last_action: 'Rejected',
    description: 'Online coding bootcamp with lifetime access.',
    commission: '35%',
  },
  {
    id: 'prog-006',
    name: 'CloudBackup Pro',
    network: 'ShareASale',
    url: 'https://cloudbackuppro.com/affiliate',
    status: 'Discovered',
    created_at: '2026-01-22T11:00:00Z',
    last_action: 'Discovery',
    description: 'Enterprise-grade cloud backup solution.',
    commission: '20%',
  },
];

export const mockApplications: Application[] = [
  {
    id: 'app-001',
    program_id: 'prog-002',
    status: 'PendingApproval',
    agent_status: 'WaitingForUserApproval',
    response_pool_used: ['rp-001', 'rp-002'],
    created_at: '2026-01-22T09:00:00Z',
    program: mockPrograms[1],
  },
  {
    id: 'app-002',
    program_id: 'prog-003',
    status: 'Approved',
    agent_status: 'Completed',
    response_pool_used: ['rp-001'],
    created_at: '2026-01-20T14:30:00Z',
    program: mockPrograms[2],
  },
];

export const mockTasks: Task[] = [
  {
    id: 'task-001',
    type: 'APPLY_PROGRAM',
    payload: { program_id: 'prog-001', profile_id: 'profile-001' },
    status: 'PENDING',
    created_at: '2026-01-22T09:00:00Z',
    logs: [],
  },
  {
    id: 'task-002',
    type: 'DISCOVER_PROGRAMS',
    payload: { keyword: 'AI tools', network: 'ClickBank' },
    status: 'RUNNING',
    created_at: '2026-01-22T08:30:00Z',
    logs: ['Started discovery...', 'Found 12 programs matching criteria'],
  },
  {
    id: 'task-003',
    type: 'APPLY_PROGRAM',
    payload: { program_id: 'prog-004', profile_id: 'profile-001' },
    status: 'PAUSED_FOR_CAPTCHA',
    created_at: '2026-01-22T07:00:00Z',
    logs: ['Application started', 'Captcha detected - waiting for user input'],
  },
];

export const mockResponsePool: ResponsePoolItem[] = [
  {
    id: 'rp-001',
    question_text: 'Describe your traffic sources',
    answer_text: 'Organic YouTube content, SEO-optimized blog posts, and engaged social media channels with 50k+ combined followers.',
    context: ['SaaS', 'AI Tools', 'General'],
    approval_rate: 0.92,
    last_used_date: '2026-01-20T12:00:00Z',
  },
  {
    id: 'rp-002',
    question_text: 'How do you plan to promote our product?',
    answer_text: 'Through in-depth product reviews, tutorial videos, comparison articles, and targeted email campaigns to my subscriber list of 10k+ engaged users.',
    context: ['SaaS', 'Software'],
    approval_rate: 0.88,
    last_used_date: '2026-01-21T15:00:00Z',
  },
  {
    id: 'rp-003',
    question_text: 'What is your website URL?',
    answer_text: 'https://automatedonlineprofits.com - A resource for digital marketing and passive income strategies.',
    context: ['General'],
    approval_rate: 0.95,
    last_used_date: '2026-01-19T10:00:00Z',
  },
  {
    id: 'rp-004',
    question_text: 'Do you have experience in this niche?',
    answer_text: 'Yes, I have 5+ years of experience in the digital marketing and SaaS space, with proven success promoting similar products.',
    context: ['SaaS', 'Digital Marketing'],
    approval_rate: 0.85,
    last_used_date: '2026-01-18T09:00:00Z',
  },
];

export const mockActivityFeed = [
  { id: '1', type: 'discovery', message: 'Discovered 6 new programs matching "AI tools"', timestamp: '2026-01-22T10:30:00Z' },
  { id: '2', type: 'application', message: 'Application submitted for CryptoTrader AI', timestamp: '2026-01-22T09:15:00Z' },
  { id: '3', type: 'approval', message: 'FitnessPro 360 application approved!', timestamp: '2026-01-21T16:00:00Z' },
  { id: '4', type: 'agent', message: 'Local agent connected successfully', timestamp: '2026-01-21T08:00:00Z' },
  { id: '5', type: 'discovery', message: 'Discovered 3 new programs on ClickBank', timestamp: '2026-01-20T14:00:00Z' },
];
