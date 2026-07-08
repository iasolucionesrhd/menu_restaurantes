import { api } from "./client";
import type { MenuPublico, MesaPublica } from "../types";

export function getMenuPublico(slug: string) {
  return api.get<MenuPublico>(`/public/${slug}/menu`);
}

export function getMesaPublica(slug: string, codigoQr: string) {
  return api.get<MesaPublica>(`/public/${slug}/mesa/${codigoQr}`);
}
