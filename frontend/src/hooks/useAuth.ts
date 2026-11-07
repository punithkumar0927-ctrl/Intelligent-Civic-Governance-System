import { create } from "zustand";
import { persist } from "zustand/middleware";
import { authService } from "../services/authService";
import type { User, LoginPayload, RegisterPayload } from "../types/user";

interface AuthStore {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  login: (payload: LoginPayload) => Promise<void>;
  register: (payload: RegisterPayload) => Promise<void>;
  logout: () => void;
  fetchMe: () => Promise<void>;
}

export const useAuth = create<AuthStore>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      login: async (payload) => {
        set({ isLoading: true, error: null });
        try {
          const result = await authService.login(payload);
          set({ token: result.access_token, user: result.user, isAuthenticated: true });
        } catch (err: unknown) {
          const msg = err instanceof Error ? err.message : "Login failed";
          set({ error: msg, isLoading: false });
          throw err;
        } finally {
          set({ isLoading: false });
        }
      },

      register: async (payload) => {
        set({ isLoading: true, error: null });
        try {
          // Backend returns a Token response with access_token + user.
          // authService.register also stores nexus_token in localStorage for the axios interceptor.
          const result = await authService.register(payload);
          set({ token: result.access_token, user: result.user, isAuthenticated: true });
        } catch (err: unknown) {
          const msg = err instanceof Error ? err.message : "Registration failed";
          set({ error: msg });
          throw err;
        } finally {
          set({ isLoading: false });
        }
      },

      logout: () => {
        authService.logout();
        set({ user: null, token: null, isAuthenticated: false, error: null });
      },

      fetchMe: async () => {
        const token = authService.getToken();
        if (!token) return;
        try {
          const user = await authService.me();
          set({ user, token, isAuthenticated: true });
        } catch {
          authService.logout();
          set({ user: null, token: null, isAuthenticated: false });
        }
      },
    }),
    {
      name: "nexus-auth",
      partialize: (state) => ({ token: state.token, user: state.user, isAuthenticated: state.isAuthenticated }),
    }
  )
);
