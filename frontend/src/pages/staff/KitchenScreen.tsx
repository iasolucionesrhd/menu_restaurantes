import { useEffect, useState } from "react";
import { useAuth } from "../../context/AuthContext";
import { useKitchenSocket } from "../../hooks/useKitchenSocket";
import { listarPedidosStaff, actualizarEstadoPedido } from "../../api/staff";
import { StatusColumn } from "../../components/kitchen/StatusColumn";
import type { EstadoPedido, Pedido } from "../../types";

const ESTADOS_ACTIVOS: EstadoPedido[] = ["recibido", "en_cocina", "listo"];

export function KitchenScreen() {
  const { usuario, logout } = useAuth();
  const [pedidos, setPedidos] = useState<Pedido[]>([]);
  const [cargando, setCargando] = useState(true);

  useEffect(() => {
    listarPedidosStaff(ESTADOS_ACTIVOS)
      .then(setPedidos)
      .finally(() => setCargando(false));
  }, []);

  const { conectado } = useKitchenSocket(usuario?.restaurante_slug, {
    onNuevoPedido: (pedido) => setPedidos((prev) => [...prev, pedido]),
    onEstadoActualizado: (pedidoId, estado) =>
      setPedidos((prev) =>
        ESTADOS_ACTIVOS.includes(estado)
          ? prev.map((p) => (p.id === pedidoId ? { ...p, estado } : p))
          : prev.filter((p) => p.id !== pedidoId)
      ),
  });

  const avanzar = async (pedidoId: number, estado: EstadoPedido) => {
    await actualizarEstadoPedido(pedidoId, estado);
  };

  if (cargando) {
    return <p className="estado-carga">Cargando pedidos...</p>;
  }

  return (
    <div className="kitchen-screen">
      <h2>Pantalla de cocina</h2>
      <button type="button" className="btn-secundario" onClick={logout}>
        Cerrar sesión
      </button>
      {!conectado && <p className="ws-banner">Reconectando en tiempo real...</p>}
      <div className="kitchen-columnas">
        <StatusColumn
          titulo="Recibido"
          pedidos={pedidos.filter((p) => p.estado === "recibido")}
          onAvanzar={avanzar}
        />
        <StatusColumn
          titulo="En cocina"
          pedidos={pedidos.filter((p) => p.estado === "en_cocina")}
          onAvanzar={avanzar}
        />
        <StatusColumn titulo="Listo" pedidos={pedidos.filter((p) => p.estado === "listo")} onAvanzar={avanzar} />
      </div>
    </div>
  );
}
