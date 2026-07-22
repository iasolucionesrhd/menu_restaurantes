import { useEffect, useState } from "react";
import { useAuth } from "../../context/AuthContext";
import { useKitchenSocket } from "../../hooks/useKitchenSocket";
import { listarPedidosStaff, marcarPagado, getResumenCaja, cerrarCaja, listarCierresCaja } from "../../api/staff";
import { formatMoney } from "../../utils/format";
import type { CierreCaja, Pedido, ResumenCaja } from "../../types";

function FilaCierre({ cierre }: { cierre: CierreCaja }) {
  return (
    <li className="ticket-card">
      <strong>{new Date(cierre.hasta).toLocaleString("es-CR")}</strong>
      <ul>
        {Number(cierre.total_efectivo) > 0 && (
          <li>
            Efectivo: {formatMoney(cierre.total_efectivo)} ({cierre.cantidad_efectivo})
          </li>
        )}
        {Number(cierre.total_tarjeta) > 0 && (
          <li>
            Tarjeta: {formatMoney(cierre.total_tarjeta)} ({cierre.cantidad_tarjeta})
          </li>
        )}
        {Number(cierre.total_sinpe) > 0 && (
          <li>
            SINPE: {formatMoney(cierre.total_sinpe)} ({cierre.cantidad_sinpe})
          </li>
        )}
        {Number(cierre.total_apple_pay) > 0 && (
          <li>
            Apple Pay: {formatMoney(cierre.total_apple_pay)} ({cierre.cantidad_apple_pay})
          </li>
        )}
      </ul>
      <strong>
        Total: {formatMoney(cierre.total_general)} ({cierre.cantidad_general} pedidos)
      </strong>
    </li>
  );
}

export function CajaScreen() {
  const { usuario, logout } = useAuth();
  const [pendientes, setPendientes] = useState<Pedido[]>([]);
  const [resumen, setResumen] = useState<ResumenCaja | null>(null);
  const [cierres, setCierres] = useState<CierreCaja[]>([]);
  const [cargando, setCargando] = useState(true);
  const [cerrando, setCerrando] = useState(false);
  const [mostrarHistorial, setMostrarHistorial] = useState(false);

  const cargar = () => {
    listarPedidosStaff([], false).then(setPendientes);
    getResumenCaja().then(setResumen);
    listarCierresCaja().then(setCierres);
  };

  useEffect(() => {
    Promise.all([
      listarPedidosStaff([], false).then(setPendientes),
      getResumenCaja().then(setResumen),
      listarCierresCaja().then(setCierres),
    ]).finally(() => setCargando(false));
  }, []);

  const { conectado } = useKitchenSocket(usuario?.restaurante_slug, {
    onNuevoPedido: () => cargar(),
    onEstadoActualizado: () => cargar(),
  });

  const cobrar = async (pedidoId: number) => {
    await marcarPagado(pedidoId);
    cargar();
  };

  const cerrar = async () => {
    if (!resumen || resumen.pedidos_periodo_actual === 0) return;
    setCerrando(true);
    try {
      await cerrarCaja();
      cargar();
    } finally {
      setCerrando(false);
    }
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
        <div className="ticket-card">
          <strong>
            Por cerrar: {formatMoney(resumen.cobrado_periodo_actual)} ({resumen.pedidos_periodo_actual} pedidos)
          </strong>
          <div className="ticket-card-acciones">
            <button
              type="button"
              className="btn-primario"
              disabled={cerrando || resumen.pedidos_periodo_actual === 0}
              onClick={cerrar}
            >
              {cerrando ? "Cerrando..." : "Cerrar caja"}
            </button>
            <button type="button" className="btn-secundario" onClick={() => setMostrarHistorial(!mostrarHistorial)}>
              {mostrarHistorial ? "Ocultar historial" : "Ver historial de cierres"}
            </button>
          </div>
        </div>
      )}
      {mostrarHistorial && (
        <div className="kitchen-columna">
          <h3>Cierres anteriores ({cierres.length})</h3>
          <ul>
            {cierres.map((c) => (
              <FilaCierre key={c.id} cierre={c} />
            ))}
          </ul>
        </div>
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
