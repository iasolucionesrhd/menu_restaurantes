import type { EstadoPedido, Pedido } from "../../types";
import { TicketCard } from "./TicketCard";

export function StatusColumn({
  titulo,
  pedidos,
  onAvanzar,
}: {
  titulo: string;
  pedidos: Pedido[];
  onAvanzar: (pedidoId: number, estado: EstadoPedido) => void;
}) {
  return (
    <div className="kitchen-columna">
      <h3>
        {titulo} ({pedidos.length})
      </h3>
      {pedidos.map((pedido) => (
        <TicketCard key={pedido.id} pedido={pedido} onAvanzar={onAvanzar} />
      ))}
    </div>
  );
}
