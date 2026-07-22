import { api } from "./client";
import type { CartItem, MetodoPago, Pedido } from "../types";

export interface DatosFacturacionInput {
  nombre: string;
  cedula: string;
  correo?: string;
  telefono?: string;
  direccion: string;
  actividad_economica?: string;
}

export interface ClienteInput {
  nombre: string;
  correo?: string;
  telefono?: string;
  consentimiento_datos: boolean;
  consentimiento_marketing: boolean;
  google_id_token?: string;
  datos_facturacion?: DatosFacturacionInput;
}

export interface CrearPedidoInput {
  mesaCodigoQr: string | null;
  cliente: ClienteInput;
  metodoPago: MetodoPago;
  items: CartItem[];
  paymentIntentId?: string;
}

export function crearPedido(slug: string, input: CrearPedidoInput) {
  return api.post<Pedido>(`/public/${slug}/pedidos`, {
    mesa_codigo_qr: input.mesaCodigoQr,
    cliente: input.cliente,
    metodo_pago: input.metodoPago,
    items: input.items.map((i) => ({
      item_id: i.itemId,
      cantidad: i.cantidad,
      notas: i.notas,
      modificador_ids: (i.modificadores ?? []).map((m) => m.modificadorId),
    })),
    payment_intent_id: input.paymentIntentId,
  });
}

export function getPedido(slug: string, pedidoId: number) {
  return api.get<Pedido>(`/public/${slug}/pedidos/${pedidoId}`);
}
