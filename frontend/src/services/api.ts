import axios, { AxiosInstance } from 'axios';
import { Issue, IssueList, DashboardStats, User, Evidence, AIAnalysisResult, ReportFormData } from '../types';

const API_BASE = '/api';

/** Turn FastAPI errors, including validation lists, into a sentence. */
export function apiErrorMessage(err: unknown, fallback: string): string {
  const response = (err as { response?: { data?: { detail?: unknown } } })?.response;
  if (!response) {
    return 'The API is not reachable. Start the backend, then try again.';
  }
  const detail = response.data?.detail;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) {
    const text = detail
      .map((item) => (item && typeof item === 'object' && 'msg' in item ? String((item as { msg: string }).msg) : ''))
      .filter(Boolean)
      .join(' ');
    if (text) return text;
  }
  return fallback;
}

// ── Create Axios instance ────────────────────────────────────────────────────
const api: AxiosInstance = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
  timeout: 30000,
});

// ── Attach JWT token to every request ───────────────────────────────────────
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('nexus_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// ── Handle 401 globally ──────────────────────────────────────────────────────
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('nexus_token');
      localStorage.removeItem('nexus_user');
      window.location.href = '/login';
    }
    return Promise.reject(err);
  }
);

// ── Auth APIs ────────────────────────────────────────────────────────────────
export const authApi = {
  register: async (data: {
    username: string; email: string; password: string;
    full_name?: string; phone?: string;
  }): Promise<{ access_token: string; user: User; dev_verification_token?: string }> => {
    const res = await api.post('/auth/register', data);
    return res.data;
  },

  login: async (email: string, password: string, remember = false): Promise<{ access_token: string; user: User }> => {
    const form = new URLSearchParams();
    form.append('username', email);
    form.append('password', password);
    const res = await api.post(`/auth/login?remember=${remember ? 'true' : 'false'}`, form, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });
    return res.data;
  },

  me: async (): Promise<User> => {
    const res = await api.get('/auth/me');
    return res.data;
  },

  logout: async (): Promise<void> => {
    await api.post('/auth/logout');
    localStorage.removeItem('nexus_token');
    localStorage.removeItem('nexus_user');
  },
};

// ── Report APIs ──────────────────────────────────────────────────────────────
export const reportApi = {
  create: async (
    data: ReportFormData,
    imageBefore?: File,
    imageAfter?: File
  ): Promise<Issue> => {
    const form = new FormData();
    form.append('title', data.title);
    if (data.description) form.append('description', data.description);
    form.append('category', data.category);
    if (data.latitude  !== undefined) form.append('latitude',  String(data.latitude));
    if (data.longitude !== undefined) form.append('longitude', String(data.longitude));
    if (data.ward)  form.append('ward',  data.ward);
    if (data.city)  form.append('city',  data.city);
    if (data.state) form.append('state', data.state);
    if (data.address_raw) form.append('address_raw', data.address_raw);
    if (imageBefore) form.append('image_before', imageBefore);
    if (imageAfter)  form.append('image_after',  imageAfter);

    const res = await api.post('/reports', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return res.data;
  },

  list: async (page = 1, perPage = 20, filters: Record<string, string> = {}): Promise<IssueList> => {
    const res = await api.get('/reports', { params: { page, per_page: perPage, ...filters } });
    return res.data;
  },

  get: async (id: number): Promise<Issue> => {
    const res = await api.get(`/reports/${id}`);
    return res.data;
  },

  update: async (id: number, data: Partial<Issue>): Promise<Issue> => {
    const res = await api.patch(`/reports/${id}`, data);
    return res.data;
  },

  upvote: async (id: number): Promise<Issue> => {
    const res = await api.post(`/reports/${id}/upvote`);
    return res.data;
  },

  getEvidence: async (issueId: number): Promise<Evidence[]> => {
    const res = await api.get(`/reports/${issueId}/evidence`);
    return res.data;
  },

  analyze: async (issueId: number): Promise<AIAnalysisResult> => {
    const res = await api.post(`/reports/${issueId}/analyze`);
    return res.data;
  },

  remove: async (id: number): Promise<{ deleted: number; file_errors: string[] }> => {
    const res = await api.delete(`/reports/${id}`);
    return res.data;
  },

  removeMany: async (ids: number[]): Promise<{ deleted: number; file_errors: string[] }> => {
    const res = await api.post('/reports/delete', { ids });
    return res.data;
  },

  removeAllMine: async (): Promise<{ deleted: number; file_errors: string[] }> => {
    const res = await api.post('/reports/delete', { delete_all: true, confirm: 'DELETE ALL' });
    return res.data;
  },
};

// ── Analytics APIs ───────────────────────────────────────────────────────────
export const analyticsApi = {
  dashboard: async (city?: string): Promise<DashboardStats> => {
    const res = await api.get('/analytics/dashboard', { params: { city } });
    return res.data;
  },

  trends: async (months = 12): Promise<{ month: string; total: number; resolved: number }[]> => {
    const res = await api.get('/analytics/trends', { params: { months } });
    return res.data;
  },
};

// ── Health ───────────────────────────────────────────────────────────────────
export const healthApi = {
  check: async () => (await api.get('/health')).data,
};

export default api;
