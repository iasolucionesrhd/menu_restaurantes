import { api } from "./client";

export interface Categoria {
  id: number;
  nombre: string;
  orden: number;
}

export interface Item {
  id: number;
  categoria_id: number;
  nombre: string;
  descripcion: string | null;
  precio: string;
  disponible: boolean;
  imagen_url: string | null;
}

export interface Mesa {
  id: number;
  numero: number | null;
  codigo_qr: string;
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
};
