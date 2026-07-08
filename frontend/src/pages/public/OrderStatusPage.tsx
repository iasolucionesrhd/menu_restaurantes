import { useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { getPedido } from "../../api/pedidos";
import { formatMoney } from "../../utils/format";
import type { EstadoPedido } from "../../types";

const ETIQUETAS_ESTADO: Record<EstadoPedido, string> = {
  recibido: "Recibido",
  en_cocina: "En preparación",
  listo: "¡Listo!",
  entregado: "Entregado",
  cancelado: "Cancelado",
};

export function OrderStatusPage() {
  const { slug, pedidoId } = useParams<{ slug: string; pedidoId: string }>();

  const query = useQuery({
    queryKey: ["pedido", slug, pedidoId],
    queryFn: () => getPedido(slug!, Number(pedidoId)),
    enabled: !!slug && !!pedidoId,
    refetchInterval: 5000,
  });

  if (query.isLoading) {
    return <p className="estado-carga">Cargando estado del pedido...</p>;
  }
  if (query.isError || !query.data) {
    return <p className="estado-error">No se encontró el pedido.</p>;
  }

  const pedido = query.data;

  return (
    <div className="checkout-page">
      <h2>Pedido #{pedido.id}</h2>
      <p className="menu-subtitulo">Estado: {ETIQUETAS_ESTADO[pedido.estado]}</p>
      <div className="checkout-resumen">
        {pedido.items.map((item) => (
          <div key={item.id}>
            {item.cantidad}× {item.nombre}
            {item.notas ? ` (${item.notas})` : ""}
          </div>
        ))}
        <p>
          <strong>Total: {formatMoney(pedido.monto_total)}</strong>
        </p>
      </div>
      {pedido.tipo_entrega === "retiro" && pedido.estado === "listo" && (
        <p className="estado-error" style={{ color: "green" }}>
          Tu pedido está listo para retirar.
        </p>
      )}
    </div>
  );
}
