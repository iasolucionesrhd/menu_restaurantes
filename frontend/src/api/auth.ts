import { api } from "./client";
import type { Sucursal, Usuario } from "../types";

export interface TokenResponse {
  access_token: string;
  token_type: string;
  usuario: Usuario;
}

export function login(email: string, password: string) {
  return api.post<TokenResponse>("/auth/login", { email, password });
}

export function listarMisRestaurantes() {
  return api.get<Sucursal[]>("/auth/mis-restaurantes");
}

export function cambiarRestaurante(restauranteId: number) {
  return api.post<TokenResponse>("/auth/cambiar-restaurante", { restaurante_id: restauranteId });
}
