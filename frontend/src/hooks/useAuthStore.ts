import { create } from 'zustand';
import { User } from '../types';
import { apiErrorMessage, authApi } from '../services/api';

/** Read persisted user object from localStorage (safe on SSR / first load). */
function _readStoredUser(): User | null {
  try {
    const raw = localStorage.getItem('nexus_user');
    return raw ? (JSON.parse(raw) as User) : null;
  } catch {
    return null;
  }
}

interface AuthStore {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  error: string | null;
  login: (email: string, password: string, remember?: boolean) => Promise<void>;
  register: (data: {
    username: string; email: string; password: string;
    full_name?: string; phone?: string;
  }) => Promise<{ dev_verification_token?: string }>;
  logout: () => Promise<void>;
  loadSession: () => void;
}

export const useAuthStore = create<AuthStore>()((set) => ({
  // Initialise from localStorage so there is no null-flash on hard refresh.
  user: _readStoredUser(),
  token: localStorage.getItem('nexus_token'),
  isLoading: false,
  error: null,

  loadSession: () => {
    const token = localStorage.getItem('nexus_token');
    const userStr = localStorage.getItem('nexus_user');
    if (token && userStr) {
      try {
        set({ token, user: JSON.parse(userStr) });
      } catch {
        set({ token: null, user: null });
      }
    }
  },

  login: async (email, password, remember = false) => {
    set({ isLoading: true, error: null });
    try {
      const res = await authApi.login(email, password, remember);
      localStorage.setItem('nexus_token', res.access_token);
      localStorage.setItem('nexus_user', JSON.stringify(res.user));
      set({ token: res.access_token, user: res.user, isLoading: false });
    } catch (err: unknown) {
      const msg = apiErrorMessage(err, 'Login failed');
      set({ error: msg, isLoading: false });
      throw new Error(msg);
    }
  },

  register: async (data) => {
    set({ isLoading: true, error: null });
    try {
      const res = await authApi.register(data);
      localStorage.setItem('nexus_token', res.access_token);
      localStorage.setItem('nexus_user', JSON.stringify(res.user));
      set({ token: res.access_token, user: res.user, isLoading: false });
      return res;
    } catch (err: unknown) {
      const msg = apiErrorMessage(err, 'Registration failed');
      set({ error: msg, isLoading: false });
      throw new Error(msg);
    }
  },

  logout: async () => {
    try {
      await authApi.logout();
    } catch {
      // ignore network error on logout
    }
    localStorage.removeItem('nexus_token');
    localStorage.removeItem('nexus_user');
    set({ token: null, user: null });
  },
}));
