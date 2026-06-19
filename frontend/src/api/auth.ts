import { http } from "./http";

export type TokenPair = { access_token: string; refresh_token: string; token_type: "bearer" };
export type Me = { id: string; email: string; nombre: string | null; rol: "admin"|"medico"|"rrhh"; matricula: string|null; activo: boolean };

export const authApi = {
  login: (email: string, password: string) =>
    http.post<TokenPair>("/api/auth/login", { email, password }).then((r) => r.data),
  refresh: (refresh_token: string) =>
    http.post<TokenPair>("/api/auth/refresh", null, { params: { refresh_token } }).then((r) => r.data),
  me: () => http.get<Me>("/api/auth/me").then((r) => r.data),
};
