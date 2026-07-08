import { api } from "./client";
import type { Usuario } from "../types";

export interface TokenResponse {
  access_token: string;
  token_type: string;
  usuario: Usuario;
}

export function login(email: string, password: string) {
  return api.post<TokenResponse>("/auth/login", { email, password });
}
