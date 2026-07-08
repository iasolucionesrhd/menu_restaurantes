import { api } from "./client";
import type { MetodoPago } from "../types";

export interface IniciarPagoResponse {
  payment_intent_id: string;
  client_config: Record<string, unknown>;
}

export interface ConfirmarPagoResponse {
  aprobado: boolean;
  transaction_id: string | null;
}

export function iniciarPago(slug: string, monto: string, metodoPago: MetodoPago, referenciaExterna: string) {
  return api.post<IniciarPagoResponse>(`/public/${slug}/pagos/iniciar`, {
    monto,
    metodo_pago: metodoPago,
    referencia_externa: referenciaExterna,
  });
}

export function confirmarPago(slug: string, paymentIntentId: string) {
  return api.post<ConfirmarPagoResponse>(`/public/${slug}/pagos/confirmar`, {
    payment_intent_id: paymentIntentId,
  });
}
