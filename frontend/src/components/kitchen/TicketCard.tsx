import type { EstadoPedido, Pedido } from "../../types";

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
