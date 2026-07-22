import { api } from "./client";
import type { EstadoPedido, Pedido } from "../types";

export function listarPedidosStaff(estados: EstadoPedido[]) {
  const query = estados.length > 0 ? `?estado=${estados.join(",")}` : "";
  return api.get<Pedido[]>(`/staff/pedidos${query}`);
}

export function actualizarEstadoPedido(pedidoId: number, estado: EstadoPedido) {
  return api.patch<Pedido>(`/staff/pedidos/${pedidoId}/estado`, { estado });
}

export function cancelarPedido(pedidoId: number, pin?: string) {
  return api.patch<Pedido>(`/staff/pedidos/${pedidoId}/estado`, { estado: "cancelado", pin });
}
