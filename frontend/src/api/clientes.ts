import { api } from "./client";

export interface PerfilCliente {
  nombre: string;
  correo: string | null;
  telefono: string | null;
  factura_nombre: string | null;
  factura_cedula: string | null;
  factura_correo: string | null;
  factura_telefono: string | null;
  factura_direccion: string | null;
  factura_actividad_economica: string | null;
}

export function obtenerPerfilCliente(slug: string, googleIdToken: string) {
  return api.post<PerfilCliente>(`/public/${slug}/cliente/perfil`, { google_id_token: googleIdToken });
}
