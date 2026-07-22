import { api } from "./client";
import type { Rol, Sucursal } from "../types";

export interface Categoria {
  id: number;
  nombre: string;
  orden: number;
}

export interface ItemIngrediente {
  ingrediente_id: number;
  nombre: string;
  unidad: string;
  cantidad_requerida: string;
}

export interface Modificador {
  id: number;
  nombre: string;
  precio_extra: string;
}

export interface ModificadorGrupo {
  id: number;
  nombre: string;
  obligatorio: boolean;
  seleccion_multiple: boolean;
  modificadores: Modificador[];
}

export interface Item {
  id: number;
  categoria_id: number;
  nombre: string;
  descripcion: string | null;
  precio: string;
  disponible: boolean;
  imagen_url: string | null;
  ingredientes: ItemIngrediente[];
  modificador_grupos: ModificadorGrupo[];
}

export interface Ingrediente {
  id: number;
  nombre: string;
  unidad: string;
  stock_actual: string;
  stock_minimo: string;
  stock_bajo: boolean;
}

export interface Mesa {
  id: number;
  numero: number | null;
  codigo_qr: string;
}

export interface UsuarioStaff {
  id: number;
  email: string;
  rol: Rol;
}

export interface RestauranteConfig {
  id: number;
  nombre: string;
  slug: string;
  tilopay_configurado: boolean;
  pin_cancelacion_configurado: boolean;
}

export const adminApi = {
  listCategorias: () => api.get<Categoria[]>("/admin/categorias"),
  createCategoria: (nombre: string, orden: number) => api.post<Categoria>("/admin/categorias", { nombre, orden }),
  deleteCategoria: (id: number) => api.delete<void>(`/admin/categorias/${id}`),

  listItems: () => api.get<Item[]>("/admin/items"),
  createItem: (data: { categoria_id: number; nombre: string; precio: string; descripcion?: string }) =>
    api.post<Item>("/admin/items", data),
  updateItem: (id: number, data: Partial<Pick<Item, "disponible" | "precio" | "nombre">>) =>
    api.patch<Item>(`/admin/items/${id}`, data),
  deleteItem: (id: number) => api.delete<void>(`/admin/items/${id}`),

  listMesas: () => api.get<Mesa[]>("/admin/mesas"),
  createMesa: (numero: number | null) => api.post<Mesa>("/admin/mesas", { numero }),
  deleteMesa: (id: number) => api.delete<void>(`/admin/mesas/${id}`),

  listIngredientes: () => api.get<Ingrediente[]>("/admin/ingredientes"),
  createIngrediente: (data: { nombre: string; unidad: string; stock_actual: string; stock_minimo: string }) =>
    api.post<Ingrediente>("/admin/ingredientes", data),
  updateIngrediente: (id: number, data: Partial<Pick<Ingrediente, "nombre" | "unidad" | "stock_actual" | "stock_minimo">>) =>
    api.patch<Ingrediente>(`/admin/ingredientes/${id}`, data),
  deleteIngrediente: (id: number) => api.delete<void>(`/admin/ingredientes/${id}`),

  setRecetaItem: (itemId: number, ingredientes: { ingrediente_id: number; cantidad_requerida: string }[]) =>
    api.put<Item>(`/admin/items/${itemId}/ingredientes`, { ingredientes }),

  createModificadorGrupo: (
    itemId: number,
    data: { nombre: string; obligatorio: boolean; seleccion_multiple: boolean }
  ) => api.post<ModificadorGrupo>(`/admin/items/${itemId}/modificador-grupos`, data),
  deleteModificadorGrupo: (grupoId: number) => api.delete<void>(`/admin/modificador-grupos/${grupoId}`),
  createModificador: (grupoId: number, data: { nombre: string; precio_extra: string }) =>
    api.post<Modificador>(`/admin/modificador-grupos/${grupoId}/modificadores`, data),
  deleteModificador: (modificadorId: number) => api.delete<void>(`/admin/modificadores/${modificadorId}`),

  getRestaurante: () => api.get<RestauranteConfig>("/admin/restaurante"),
  setPinCancelacion: (pin: string) =>
    api.patch<RestauranteConfig>("/admin/restaurante", { pin_cancelacion: pin }),

  listUsuarios: () => api.get<UsuarioStaff[]>("/admin/usuarios"),
  createUsuario: (data: { email: string; password: string; rol: Rol }) =>
    api.post<UsuarioStaff>("/admin/usuarios", data),
  deleteUsuario: (id: number) => api.delete<void>(`/admin/usuarios/${id}`),

  createSucursal: (data: { nombre: string; slug: string }) => api.post<Sucursal>("/admin/sucursales", data),
};
