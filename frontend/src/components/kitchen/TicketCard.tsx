import { useState } from "react";
import { useAuth } from "../../context/AuthContext";
import { ApiError } from "../../api/client";
import type { EstadoPedido, MetodoPago, Pedido } from "../../types";

const SIGUIENTE_ESTADO: Partial<Record<EstadoPedido, EstadoPedido>> = {
  recibido: "en_cocina",
  en_cocina: "listo",
  listo: "entregado",
};

const ETIQUETA_ACCION: Partial<Record<EstadoPedido, string>> = {
  recibido: "Pasar a cocina",
  en_cocina: "Marcar listo",
  listo: "Marcar entregado",
};

const ETIQUETA_PAGO: Record<MetodoPago, string> = {
  efectivo_en_restaurante: "💵 Cobrar en mesa",
  tarjeta: "💳 Pagado (tarjeta)",
  sinpe: "💳 Pagado (SINPE)",
  apple_pay: "💳 Pagado (Apple Pay)",
};

const ESTADOS_CANCELABLES: EstadoPedido[] = ["recibido", "en_cocina"];

export function TicketCard({
  pedido,
  onAvanzar,
  onCancelar,
}: {
  pedido: Pedido;
  onAvanzar: (pedidoId: number, estado: EstadoPedido) => void;
  onCancelar: (pedidoId: number, pin?: string) => Promise<void>;
}) {
  const { usuario } = useAuth();
  const siguiente = SIGUIENTE_ESTADO[pedido.estado];
  const puedeCancelar = ESTADOS_CANCELABLES.includes(pedido.estado);

  const [cancelando, setCancelando] = useState(false);
  const [pin, setPin] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);

  const confirmarCancelacion = async () => {
    setEnviando(true);
    setError(null);
    try {
      await onCancelar(pedido.id, usuario?.rol === "cocina" ? pin : undefined);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudo cancelar el pedido");
    } finally {
      setEnviando(false);
    }
  };

  return (
    <div className="ticket-card">
      <strong>{pedido.tipo_entrega === "mesa" ? `Mesa ${pedido.mesa_numero}` : "Para retirar"}</strong>
      <span> — Pedido #{pedido.id}</span>
      <div>
        <span className={`pago-badge pago-badge-${pedido.metodo_pago === "efectivo_en_restaurante" ? "efectivo" : "pagado"}`}>
          {ETIQUETA_PAGO[pedido.metodo_pago]}
        </span>
      </div>
      <ul>
        {pedido.items.map((item) => (
          <li key={item.id}>
            {item.cantidad}× {item.nombre}
            {item.notas ? ` (${item.notas})` : ""}
          </li>
        ))}
      </ul>
      <div className="ticket-card-acciones">
        {siguiente && (
          <button type="button" className="btn-primario" onClick={() => onAvanzar(pedido.id, siguiente)}>
            {ETIQUETA_ACCION[pedido.estado]}
          </button>
        )}
        {puedeCancelar && !cancelando && (
          <button type="button" className="btn-peligro" onClick={() => setCancelando(true)}>
            Cancelar pedido
          </button>
        )}
      </div>
      {cancelando && (
        <div className="ticket-cancelar-form">
          <p>
            ¿Cancelar este pedido?
            {pedido.requiere_factura && " Se generará una nota de crédito interna."}
          </p>
          {usuario?.rol === "cocina" && (
            <input
              type="password"
              placeholder="Código de cancelación"
              value={pin}
              onChange={(e) => setPin(e.target.value)}
            />
          )}
          {error && <p className="ticket-cancelar-error">{error}</p>}
          <div className="ticket-card-acciones">
            <button type="button" className="btn-peligro" disabled={enviando} onClick={confirmarCancelacion}>
              Confirmar cancelación
            </button>
            <button
              type="button"
              className="btn-secundario"
              disabled={enviando}
              onClick={() => {
                setCancelando(false);
                setPin("");
                setError(null);
              }}
            >
              Volver
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
