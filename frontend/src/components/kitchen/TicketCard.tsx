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

export function TicketCard({
  pedido,
  onAvanzar,
}: {
  pedido: Pedido;
  onAvanzar: (pedidoId: number, estado: EstadoPedido) => void;
}) {
  const siguiente = SIGUIENTE_ESTADO[pedido.estado];

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
      {siguiente && (
        <button type="button" className="btn-primario" onClick={() => onAvanzar(pedido.id, siguiente)}>
          {ETIQUETA_ACCION[pedido.estado]}
        </button>
      )}
    </div>
  );
}
