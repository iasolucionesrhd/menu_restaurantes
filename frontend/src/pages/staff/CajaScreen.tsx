import { useEffect, useState } from "react";
import { useAuth } from "../../context/AuthContext";
import { useKitchenSocket } from "../../hooks/useKitchenSocket";
import { listarPedidosStaff, marcarPagado, getResumenCaja } from "../../api/staff";
import { formatMoney } from "../../utils/format";
import type { Pedido, ResumenCaja } from "../../types";

export function CajaScreen() {
  const { usuario, logout } = useAuth();
  const [pendientes, setPendientes] = useState<Pedido[]>([]);
  const [resumen, setResumen] = useState<ResumenCaja | null>(null);
  const [cargando, setCargando] = useState(true);

  const cargar = () => {
    listarPedidosStaff([], false).then(setPendientes);
    getResumenCaja().then(setResumen);
  };

  useEffect(() => {
    Promise.all([listarPedidosStaff([], false).then(setPendientes), getResumenCaja().then(setResumen)]).finally(() =>
      setCargando(false)
    );
  }, []);

  const { conectado } = useKitchenSocket(usuario?.restaurante_slug, {
    onNuevoPedido: () => cargar(),
    onEstadoActualizado: () => cargar(),
  });

  const cobrar = async (pedidoId: number) => {
    await marcarPagado(pedidoId);
    cargar();
  };

  if (cargando) {
    return <p className="estado-carga">Cargando caja...</p>;
  }

  const pendientesFiltrados = pendientes.filter((p) => p.estado !== "cancelado");

  return (
    <div className="kitchen-screen">
      <h2>Caja</h2>
      <button type="button" className="btn-secundario" onClick={logout}>
        Cerrar sesión
      </button>
      {!conectado && <p className="ws-banner">Reconectando en tiempo real...</p>}
      {resumen && (
        <p>
          <strong>
            Cobrado hoy: {formatMoney(resumen.cobrado_hoy)} ({resumen.pedidos_cobrados_hoy} pedidos)
          </strong>
        </p>
      )}
      <div className="kitchen-columna">
        <h3>Pendientes de cobro ({pendientesFiltrados.length})</h3>
        {pendientesFiltrados.map((pedido) => (
          <div key={pedido.id} className="ticket-card">
            <strong>{pedido.tipo_entrega === "mesa" ? `Mesa ${pedido.mesa_numero}` : "Para retirar"}</strong>
            <span> — Pedido #{pedido.id}</span>
            <div>
              <strong>{formatMoney(pedido.monto_total)}</strong>
            </div>
            <button type="button" className="btn-primario" onClick={() => cobrar(pedido.id)}>
              Marcar cobrado
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
