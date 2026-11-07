import api from "./api";
import type { LoginPayload, RegisterPayload, User } from "../types/user";

/** Shape of the backend's Token response (matches schemas.Token). */
interface TokenResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export const authService = {
  async login(payload: LoginPayload): Promise<TokenResponse> {
    const form = new URLSearchParams();
    form.append("username", payload.username);   // OAuth2: this is the email
    form.append("password", payload.password);
    const { data } = await api.post<TokenResponse>("/auth/login", form, {
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
    });
    localStorage.setItem("nexus_token", data.access_token);
    localStorage.setItem("nexus_user", JSON.stringify(data.user));
    return data;
  },

  async register(payload: RegisterPayload): Promise<TokenResponse> {
    const { data } = await api.post<TokenResponse>("/auth/register", payload);
    localStorage.setItem("nexus_token", data.access_token);
    localStorage.setItem("nexus_user", JSON.stringify(data.user));
    return data;
  },

  async me(): Promise<User> {
    const { data } = await api.get<User>("/auth/me");
    return data;
  },

  logout(): void {
    localStorage.removeItem("nexus_token");
    localStorage.removeItem("nexus_user");
  },

  getToken(): string | null {
    return localStorage.getItem("nexus_token");
  },
};
