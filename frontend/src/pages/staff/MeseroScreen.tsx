import { useEffect, useState } from "react";
import { useAuth } from "../../context/AuthContext";
import { useKitchenSocket } from "../../hooks/useKitchenSocket";
import { listarPedidosStaff, actualizarEstadoPedido, listMesasStaff, crearPedidoAsistido } from "../../api/staff";
import { getMenuPublico } from "../../api/menu";
import { formatMoney } from "../../utils/format";
import type { Mesa } from "../../api/admin";
import type { EstadoPedido, ItemMenu, Pedido } from "../../types";

const ESTADOS_ACTIVOS: EstadoPedido[] = ["recibido", "en_cocina", "listo"];

const ETIQUETA_ESTADO: Record<EstadoPedido, string> = {
  recibido: "Recibido",
  en_cocina: "En cocina",
  listo: "Listo — entregar",
  entregado: "Entregado",
  cancelado: "Cancelado",
};

interface LineaAsistida {
  item: ItemMenu;
  cantidad: number;
  modificadorIds: number[];
}

function TomarPedidoForm({ slug, onCreado }: { slug: string; onCreado: () => void }) {
  const [mesas, setMesas] = useState<Mesa[]>([]);
  const [items, setItems] = useState<ItemMenu[]>([]);
  const [mesaId, setMesaId] = useState("");
  const [clienteNombre, setClienteNombre] = useState("");
  const [lineas, setLineas] = useState<LineaAsistida[]>([]);
  const [seleccion, setSeleccion] = useState<Record<number, number[]>>({});
  const [enviando, setEnviando] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listMesasStaff().then(setMesas);
    getMenuPublico(slug).then((menu) => setItems(menu.categorias.flatMap((c) => c.items)));
  }, [slug]);

  const agregarLinea = (item: ItemMenu) => {
    const grupoIncompleto = item.modificador_grupos.find(
      (g) => g.obligatorio && (seleccion[g.id] ?? []).length === 0
    );
    if (grupoIncompleto) return;
    const modificadorIds = item.modificador_grupos.flatMap((g) => seleccion[g.id] ?? []);
    setLineas([...lineas, { item, cantidad: 1, modificadorIds }]);
    setSeleccion({});
  };

  const quitarLinea = (index: number) => setLineas(lineas.filter((_, i) => i !== index));

  const total = lineas.reduce((acc, l) => {
    const extras = l.modificadorIds.reduce((sum, id) => {
      const mod = l.item.modificador_grupos.flatMap((g) => g.modificadores).find((m) => m.id === id);
      return sum + (mod ? Number(mod.precio_extra) : 0);
    }, 0);
    return acc + (Number(l.item.precio) + extras) * l.cantidad;
  }, 0);

  const enviar = async () => {
    if (!mesaId || !clienteNombre.trim() || lineas.length === 0) return;
    setEnviando(true);
    setError(null);
    try {
      await crearPedidoAsistido({
        mesa_id: Number(mesaId),
        cliente_nombre: clienteNombre.trim(),
        items: lineas.map((l) => ({
          item_id: l.item.id,
          cantidad: l.cantidad,
          modificador_ids: l.modificadorIds,
        })),
      });
      setLineas([]);
      setClienteNombre("");
      setMesaId("");
      onCreado();
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo crear el pedido");
    } finally {
      setEnviando(false);
    }
  };

  return (
    <div className="receta-editor">
      <h3>Tomar pedido</h3>
      <div className="admin-form-inline">
        <select value={mesaId} onChange={(e) => setMesaId(e.target.value)}>
          <option value="">Mesa...</option>
          {mesas.map((m) => (
            <option key={m.id} value={m.id}>
              {m.numero !== null ? `Mesa ${m.numero}` : "Para retirar"}
            </option>
          ))}
        </select>
        <input
          placeholder="Nombre del cliente"
          value={clienteNombre}
          onChange={(e) => setClienteNombre(e.target.value)}
        />
      </div>
      <ul>
        {lineas.map((l, i) => (
          <li key={i}>
            {l.cantidad}× {l.item.nombre}
            {l.modificadorIds.length > 0 &&
              ` (${l.item.modificador_grupos
                .flatMap((g) => g.modificadores)
                .filter((m) => l.modificadorIds.includes(m.id))
                .map((m) => m.nombre)
                .join(", ")})`}
            <button type="button" className="btn-secundario" onClick={() => quitarLinea(i)}>
              Quitar
            </button>
          </li>
        ))}
      </ul>
      {items.map((item) => (
        <div key={item.id} className="modificador-grupo-admin">
          <strong>
            {item.nombre} — {formatMoney(item.precio)}
          </strong>
          {item.modificador_grupos.map((grupo) => (
            <div key={grupo.id} className="modificador-grupo">
              <span>
                {grupo.nombre}
                {grupo.obligatorio && <span className="modificador-obligatorio"> (obligatorio)</span>}
              </span>
              {grupo.modificadores.map((mod) => (
                <label key={mod.id} className="modificador-opcion">
                  <input
                    type={grupo.seleccion_multiple ? "checkbox" : "radio"}
                    name={`grupo-mesero-${grupo.id}`}
                    checked={(seleccion[grupo.id] ?? []).includes(mod.id)}
                    onChange={() => {
                      const actuales = seleccion[grupo.id] ?? [];
                      const nuevos = grupo.seleccion_multiple
                        ? actuales.includes(mod.id)
                          ? actuales.filter((id) => id !== mod.id)
                          : [...actuales, mod.id]
                        : [mod.id];
                      setSeleccion({ ...seleccion, [grupo.id]: nuevos });
                    }}
                  />
                  {mod.nombre}
                  {Number(mod.precio_extra) > 0 && ` (+${formatMoney(mod.precio_extra)})`}
                </label>
              ))}
            </div>
          ))}
          <button type="button" className="btn-secundario" onClick={() => agregarLinea(item)}>
            Agregar
          </button>
        </div>
      ))}
      <p>
        <strong>Total: {formatMoney(total)}</strong>
      </p>
      {error && <p className="estado-error">{error}</p>}
      <button
        type="button"
        className="btn-primario"
        disabled={enviando || !mesaId || !clienteNombre.trim() || lineas.length === 0}
        onClick={enviar}
      >
        Confirmar pedido
      </button>
    </div>
  );
}

export function MeseroScreen() {
  const { usuario, logout } = useAuth();
  const [pedidos, setPedidos] = useState<Pedido[]>([]);
  const [cargando, setCargando] = useState(true);
  const [mostrarFormulario, setMostrarFormulario] = useState(false);

  const cargarPedidos = () =>
    listarPedidosStaff(ESTADOS_ACTIVOS)
      .then(setPedidos)
      .finally(() => setCargando(false));

  useEffect(() => {
    cargarPedidos();
  }, []);

  const { conectado } = useKitchenSocket(usuario?.restaurante_slug, {
    onNuevoPedido: (pedido) => setPedidos((prev) => [...prev, pedido]),
    onEstadoActualizado: (pedido) =>
      setPedidos((prev) =>
        ESTADOS_ACTIVOS.includes(pedido.estado)
          ? prev.map((p) => (p.id === pedido.id ? pedido : p))
          : prev.filter((p) => p.id !== pedido.id)
      ),
  });

  const marcarEntregado = (pedidoId: number) => actualizarEstadoPedido(pedidoId, "entregado");

  if (cargando) {
    return <p className="estado-carga">Cargando pedidos...</p>;
  }

  return (
    <div className="kitchen-screen">
      <h2>Mesero</h2>
      <div className="ticket-card-acciones">
        <button type="button" className="btn-primario" onClick={() => setMostrarFormulario(!mostrarFormulario)}>
          {mostrarFormulario ? "Cerrar" : "Tomar pedido"}
        </button>
        <button type="button" className="btn-secundario" onClick={logout}>
          Cerrar sesión
        </button>
      </div>
      {!conectado && <p className="ws-banner">Reconectando en tiempo real...</p>}
      {mostrarFormulario && usuario && (
        <TomarPedidoForm
          slug={usuario.restaurante_slug}
          onCreado={() => {
            setMostrarFormulario(false);
            cargarPedidos();
          }}
        />
      )}
      <div className="kitchen-columna">
        <h3>Pedidos activos ({pedidos.length})</h3>
        {pedidos.map((pedido) => (
          <div key={pedido.id} className="ticket-card">
            <strong>{pedido.tipo_entrega === "mesa" ? `Mesa ${pedido.mesa_numero}` : "Para retirar"}</strong>
            <span> — Pedido #{pedido.id} — {ETIQUETA_ESTADO[pedido.estado]}</span>
            <ul>
              {pedido.items.map((item) => (
                <li key={item.id}>
                  {item.cantidad}× {item.nombre}
                  {item.modificadores.length > 0 && ` (${item.modificadores.map((m) => m.nombre).join(", ")})`}
                </li>
              ))}
            </ul>
            {pedido.estado === "listo" && (
              <button type="button" className="btn-primario" onClick={() => marcarEntregado(pedido.id)}>
                Marcar entregado
              </button>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
