import { api } from "./client";
import type { EstadoPedido, Pedido, ResumenCaja } from "../types";
import type { Mesa } from "./admin";

export function listarPedidosStaff(estados: EstadoPedido[], pagado?: boolean) {
  const params = new URLSearchParams();
  if (estados.length > 0) params.set("estado", estados.join(","));
  if (pagado !== undefined) params.set("pagado", String(pagado));
  const query = params.toString() ? `?${params.toString()}` : "";
  return api.get<Pedido[]>(`/staff/pedidos${query}`);
}

export function actualizarEstadoPedido(pedidoId: number, estado: EstadoPedido) {
  return api.patch<Pedido>(`/staff/pedidos/${pedidoId}/estado`, { estado });
}

export function cancelarPedido(pedidoId: number, pin?: string) {
  return api.patch<Pedido>(`/staff/pedidos/${pedidoId}/estado`, { estado: "cancelado", pin });
}

export function marcarPagado(pedidoId: number) {
  return api.patch<Pedido>(`/staff/pedidos/${pedidoId}/pagado`);
}

export function getResumenCaja() {
  return api.get<ResumenCaja>("/staff/pedidos/resumen-caja");
}

export function listMesasStaff() {
  return api.get<Mesa[]>("/staff/mesas");
}

export interface ItemPedidoAsistidoInput {
  item_id: number;
  cantidad: number;
  notas?: string;
  modificador_ids?: number[];
}

export function crearPedidoAsistido(data: {
  mesa_id: number;
  cliente_nombre: string;
  items: ItemPedidoAsistidoInput[];
}) {
  return api.post<Pedido>("/staff/pedidos/asistido", data);
}
