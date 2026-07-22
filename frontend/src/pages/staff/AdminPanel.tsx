import { Fragment, useEffect, useState } from "react";
import { useAuth } from "../../context/AuthContext";
import {
  adminApi,
  type Categoria,
  type Ingrediente,
  type Item,
  type Mesa,
  type RestauranteConfig,
  type UsuarioStaff,
} from "../../api/admin";
import { MesaQrImage } from "../../components/admin/MesaQrImage";
import type { Rol } from "../../types";

type Tab = "categorias" | "items" | "mesas" | "ingredientes" | "personal" | "seguridad";

const ETIQUETA_ROL: Record<Rol, string> = {
  admin: "Admin",
  cocina: "Cocina",
  mesero: "Mesero",
  cajero: "Cajero",
};

function CategoriasTab() {
  const [categorias, setCategorias] = useState<Categoria[]>([]);
  const [nombre, setNombre] = useState("");

  const cargar = () => adminApi.listCategorias().then(setCategorias);
  useEffect(() => {
    cargar();
  }, []);

  const crear = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!nombre.trim()) return;
    await adminApi.createCategoria(nombre.trim(), categorias.length);
    setNombre("");
    cargar();
  };

  return (
    <div>
      <form className="admin-form-inline" onSubmit={crear}>
        <input placeholder="Nombre de categoría" value={nombre} onChange={(e) => setNombre(e.target.value)} />
        <button type="submit" className="btn-primario">
          Agregar
        </button>
      </form>
      <table className="admin-tabla">
        <thead>
          <tr>
            <th>Nombre</th>
            <th>Orden</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {categorias.map((c) => (
            <tr key={c.id}>
              <td>{c.nombre}</td>
              <td>{c.orden}</td>
              <td>
                <button
                  type="button"
                  className="btn-secundario"
                  onClick={() => adminApi.deleteCategoria(c.id).then(cargar)}
                >
                  Eliminar
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function RecetaEditor({ item, onCerrar }: { item: Item; onCerrar: () => void }) {
  const [ingredientesDisponibles, setIngredientesDisponibles] = useState<Ingrediente[]>([]);
  const [receta, setReceta] = useState<{ ingrediente_id: number; cantidad_requerida: string }[]>(
    item.ingredientes.map((i) => ({ ingrediente_id: i.ingrediente_id, cantidad_requerida: i.cantidad_requerida }))
  );
  const [nuevoIngredienteId, setNuevoIngredienteId] = useState("");
  const [nuevaCantidad, setNuevaCantidad] = useState("");
  const [guardando, setGuardando] = useState(false);

  useEffect(() => {
    adminApi.listIngredientes().then(setIngredientesDisponibles);
  }, []);

  const nombreDe = (ingredienteId: number) =>
    ingredientesDisponibles.find((i) => i.id === ingredienteId)?.nombre ?? `#${ingredienteId}`;
  const unidadDe = (ingredienteId: number) => ingredientesDisponibles.find((i) => i.id === ingredienteId)?.unidad ?? "";

  const agregarFila = () => {
    if (!nuevoIngredienteId || !nuevaCantidad) return;
    setReceta([...receta, { ingrediente_id: Number(nuevoIngredienteId), cantidad_requerida: nuevaCantidad }]);
    setNuevoIngredienteId("");
    setNuevaCantidad("");
  };

  const guardar = async () => {
    setGuardando(true);
    try {
      await adminApi.setRecetaItem(item.id, receta);
      onCerrar();
    } finally {
      setGuardando(false);
    }
  };

  const disponiblesParaAgregar = ingredientesDisponibles.filter(
    (i) => !receta.some((r) => r.ingrediente_id === i.id)
  );

  return (
    <div className="receta-editor">
      <ul>
        {receta.map((r) => (
          <li key={r.ingrediente_id}>
            {nombreDe(r.ingrediente_id)}: {r.cantidad_requerida} {unidadDe(r.ingrediente_id)}
            <button
              type="button"
              className="btn-secundario"
              onClick={() => setReceta(receta.filter((x) => x.ingrediente_id !== r.ingrediente_id))}
            >
              Quitar
            </button>
          </li>
        ))}
      </ul>
      <div className="admin-form-inline">
        <select value={nuevoIngredienteId} onChange={(e) => setNuevoIngredienteId(e.target.value)}>
          <option value="">Ingrediente...</option>
          {disponiblesParaAgregar.map((i) => (
            <option key={i.id} value={i.id}>
              {i.nombre} ({i.unidad})
            </option>
          ))}
        </select>
        <input
          placeholder="Cantidad requerida"
          value={nuevaCantidad}
          onChange={(e) => setNuevaCantidad(e.target.value)}
        />
        <button type="button" className="btn-secundario" onClick={agregarFila}>
          Agregar a receta
        </button>
      </div>
      <div className="ticket-card-acciones">
        <button type="button" className="btn-primario" disabled={guardando} onClick={guardar}>
          Guardar receta
        </button>
        <button type="button" className="btn-secundario" onClick={onCerrar}>
          Cerrar
        </button>
      </div>
    </div>
  );
}

function ModificadorEditor({ item, onCambio }: { item: Item; onCambio: () => void }) {
  const [nuevoGrupo, setNuevoGrupo] = useState({ nombre: "", obligatorio: false, seleccion_multiple: false });
  const [nuevaOpcion, setNuevaOpcion] = useState<Record<number, { nombre: string; precio_extra: string }>>({});

  const crearGrupo = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!nuevoGrupo.nombre.trim()) return;
    await adminApi.createModificadorGrupo(item.id, nuevoGrupo);
    setNuevoGrupo({ nombre: "", obligatorio: false, seleccion_multiple: false });
    onCambio();
  };

  const crearOpcion = async (grupoId: number) => {
    const datos = nuevaOpcion[grupoId];
    if (!datos?.nombre.trim()) return;
    await adminApi.createModificador(grupoId, {
      nombre: datos.nombre.trim(),
      precio_extra: datos.precio_extra || "0",
    });
    setNuevaOpcion({ ...nuevaOpcion, [grupoId]: { nombre: "", precio_extra: "" } });
    onCambio();
  };

  return (
    <div className="receta-editor">
      {item.modificador_grupos.map((grupo) => (
        <div key={grupo.id} className="modificador-grupo-admin">
          <div>
            <strong>{grupo.nombre}</strong>{" "}
            <span className="modificador-obligatorio">
              {grupo.obligatorio ? "obligatorio" : "opcional"} ·{" "}
              {grupo.seleccion_multiple ? "selección múltiple" : "selección única"}
            </span>
            <button
              type="button"
              className="btn-secundario"
              onClick={() => adminApi.deleteModificadorGrupo(grupo.id).then(onCambio)}
            >
              Eliminar grupo
            </button>
          </div>
          <ul>
            {grupo.modificadores.map((mod) => (
              <li key={mod.id}>
                {mod.nombre} (+{mod.precio_extra})
                <button
                  type="button"
                  className="btn-secundario"
                  onClick={() => adminApi.deleteModificador(mod.id).then(onCambio)}
                >
                  Quitar
                </button>
              </li>
            ))}
          </ul>
          <div className="admin-form-inline">
            <input
              placeholder="Nombre de la opción"
              value={nuevaOpcion[grupo.id]?.nombre ?? ""}
              onChange={(e) =>
                setNuevaOpcion({
                  ...nuevaOpcion,
                  [grupo.id]: { nombre: e.target.value, precio_extra: nuevaOpcion[grupo.id]?.precio_extra ?? "" },
                })
              }
            />
            <input
              placeholder="Precio extra"
              value={nuevaOpcion[grupo.id]?.precio_extra ?? ""}
              onChange={(e) =>
                setNuevaOpcion({
                  ...nuevaOpcion,
                  [grupo.id]: { nombre: nuevaOpcion[grupo.id]?.nombre ?? "", precio_extra: e.target.value },
                })
              }
            />
            <button type="button" className="btn-secundario" onClick={() => crearOpcion(grupo.id)}>
              Agregar opción
            </button>
          </div>
        </div>
      ))}
      <form className="admin-form-inline" onSubmit={crearGrupo}>
        <input
          placeholder="Nuevo grupo (ej. Tamaño)"
          value={nuevoGrupo.nombre}
          onChange={(e) => setNuevoGrupo({ ...nuevoGrupo, nombre: e.target.value })}
        />
        <label className="modificador-opcion">
          <input
            type="checkbox"
            checked={nuevoGrupo.obligatorio}
            onChange={(e) => setNuevoGrupo({ ...nuevoGrupo, obligatorio: e.target.checked })}
          />
          Obligatorio
        </label>
        <label className="modificador-opcion">
          <input
            type="checkbox"
            checked={nuevoGrupo.seleccion_multiple}
            onChange={(e) => setNuevoGrupo({ ...nuevoGrupo, seleccion_multiple: e.target.checked })}
          />
          Selección múltiple
        </label>
        <button type="submit" className="btn-primario">
          Crear grupo
        </button>
      </form>
    </div>
  );
}

function ItemsTab() {
  const [items, setItems] = useState<Item[]>([]);
  const [categorias, setCategorias] = useState<Categoria[]>([]);
  const [form, setForm] = useState({ nombre: "", precio: "", categoria_id: "" });
  const [recetaVisibleId, setRecetaVisibleId] = useState<number | null>(null);
  const [modificadoresVisibleId, setModificadoresVisibleId] = useState<number | null>(null);

  const cargar = () => {
    adminApi.listItems().then(setItems);
    adminApi.listCategorias().then(setCategorias);
  };
  useEffect(cargar, []);

  const crear = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.nombre.trim() || !form.precio || !form.categoria_id) return;
    await adminApi.createItem({
      nombre: form.nombre.trim(),
      precio: form.precio,
      categoria_id: Number(form.categoria_id),
    });
    setForm({ nombre: "", precio: "", categoria_id: "" });
    cargar();
  };

  return (
    <div>
      <form className="admin-form-inline" onSubmit={crear}>
        <input
          placeholder="Nombre"
          value={form.nombre}
          onChange={(e) => setForm({ ...form, nombre: e.target.value })}
        />
        <input
          placeholder="Precio"
          value={form.precio}
          onChange={(e) => setForm({ ...form, precio: e.target.value })}
        />
        <select value={form.categoria_id} onChange={(e) => setForm({ ...form, categoria_id: e.target.value })}>
          <option value="">Categoría...</option>
          {categorias.map((c) => (
            <option key={c.id} value={c.id}>
              {c.nombre}
            </option>
          ))}
        </select>
        <button type="submit" className="btn-primario">
          Agregar
        </button>
      </form>
      <table className="admin-tabla">
        <thead>
          <tr>
            <th>Nombre</th>
            <th>Precio</th>
            <th>Disponible</th>
            <th>Receta</th>
            <th>Modificadores</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <Fragment key={item.id}>
              <tr>
                <td>{item.nombre}</td>
                <td>
                  <input
                    className="admin-precio-input"
                    type="number"
                    step="0.01"
                    min="0"
                    defaultValue={item.precio}
                    onBlur={(e) => {
                      if (e.target.value && e.target.value !== item.precio) {
                        adminApi.updateItem(item.id, { precio: e.target.value }).then(cargar);
                      }
                    }}
                  />
                </td>
                <td>
                  <input
                    type="checkbox"
                    checked={item.disponible}
                    onChange={(e) => adminApi.updateItem(item.id, { disponible: e.target.checked }).then(cargar)}
                  />
                </td>
                <td>
                  <button
                    type="button"
                    className="btn-secundario"
                    onClick={() => setRecetaVisibleId(recetaVisibleId === item.id ? null : item.id)}
                  >
                    {item.ingredientes.length > 0 ? `Receta (${item.ingredientes.length})` : "Definir receta"}
                  </button>
                </td>
                <td>
                  <button
                    type="button"
                    className="btn-secundario"
                    onClick={() => setModificadoresVisibleId(modificadoresVisibleId === item.id ? null : item.id)}
                  >
                    {item.modificador_grupos.length > 0
                      ? `Modificadores (${item.modificador_grupos.length})`
                      : "Definir modificadores"}
                  </button>
                </td>
                <td>
                  <button
                    type="button"
                    className="btn-secundario"
                    onClick={() => adminApi.deleteItem(item.id).then(cargar)}
                  >
                    Eliminar
                  </button>
                </td>
              </tr>
              {recetaVisibleId === item.id && (
                <tr>
                  <td colSpan={6}>
                    <RecetaEditor
                      item={item}
                      onCerrar={() => {
                        setRecetaVisibleId(null);
                        cargar();
                      }}
                    />
                  </td>
                </tr>
              )}
              {modificadoresVisibleId === item.id && (
                <tr>
                  <td colSpan={6}>
                    <ModificadorEditor item={item} onCambio={cargar} />
                  </td>
                </tr>
              )}
            </Fragment>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function MesasTab() {
  const [mesas, setMesas] = useState<Mesa[]>([]);
  const [numero, setNumero] = useState("");
  const [qrVisibleId, setQrVisibleId] = useState<number | null>(null);

  const cargar = () => {
    adminApi.listMesas().then(setMesas);
  };
  useEffect(cargar, []);

  const crear = async (e: React.FormEvent) => {
    e.preventDefault();
    await adminApi.createMesa(numero.trim() ? Number(numero) : null);
    setNumero("");
    cargar();
  };

  return (
    <div>
      <form className="admin-form-inline" onSubmit={crear}>
        <input
          placeholder="Número de mesa (vacío = para retirar)"
          value={numero}
          onChange={(e) => setNumero(e.target.value)}
        />
        <button type="submit" className="btn-primario">
          Agregar mesa
        </button>
      </form>
      <table className="admin-tabla">
        <thead>
          <tr>
            <th>Mesa</th>
            <th>QR</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {mesas.map((mesa) => (
            <tr key={mesa.id}>
              <td>{mesa.numero !== null ? `Mesa ${mesa.numero}` : "Para retirar"}</td>
              <td>
                {qrVisibleId === mesa.id ? (
                  <MesaQrImage mesaId={mesa.id} />
                ) : (
                  <button type="button" className="btn-secundario" onClick={() => setQrVisibleId(mesa.id)}>
                    Ver QR
                  </button>
                )}
              </td>
              <td>
                <button
                  type="button"
                  className="btn-secundario"
                  onClick={() => adminApi.deleteMesa(mesa.id).then(cargar)}
                >
                  Eliminar
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function IngredientesTab() {
  const [ingredientes, setIngredientes] = useState<Ingrediente[]>([]);
  const [form, setForm] = useState({ nombre: "", unidad: "", stock_actual: "", stock_minimo: "" });

  const cargar = () => adminApi.listIngredientes().then(setIngredientes);
  useEffect(() => {
    cargar();
  }, []);

  const crear = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.nombre.trim() || !form.unidad.trim()) return;
    await adminApi.createIngrediente({
      nombre: form.nombre.trim(),
      unidad: form.unidad.trim(),
      stock_actual: form.stock_actual || "0",
      stock_minimo: form.stock_minimo || "0",
    });
    setForm({ nombre: "", unidad: "", stock_actual: "", stock_minimo: "" });
    cargar();
  };

  return (
    <div>
      <form className="admin-form-inline" onSubmit={crear}>
        <input
          placeholder="Nombre"
          value={form.nombre}
          onChange={(e) => setForm({ ...form, nombre: e.target.value })}
        />
        <input
          placeholder="Unidad (g, ml, unidad...)"
          value={form.unidad}
          onChange={(e) => setForm({ ...form, unidad: e.target.value })}
        />
        <input
          placeholder="Stock inicial"
          value={form.stock_actual}
          onChange={(e) => setForm({ ...form, stock_actual: e.target.value })}
        />
        <input
          placeholder="Stock mínimo"
          value={form.stock_minimo}
          onChange={(e) => setForm({ ...form, stock_minimo: e.target.value })}
        />
        <button type="submit" className="btn-primario">
          Agregar
        </button>
      </form>
      <table className="admin-tabla">
        <thead>
          <tr>
            <th>Nombre</th>
            <th>Unidad</th>
            <th>Stock actual</th>
            <th>Stock mínimo</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {ingredientes.map((ing) => (
            <tr key={ing.id} className={ing.stock_bajo ? "fila-stock-bajo" : ""}>
              <td>{ing.nombre}</td>
              <td>{ing.unidad}</td>
              <td>
                <input
                  className="admin-precio-input"
                  type="number"
                  step="0.01"
                  defaultValue={ing.stock_actual}
                  onBlur={(e) => {
                    if (e.target.value && e.target.value !== ing.stock_actual) {
                      adminApi.updateIngrediente(ing.id, { stock_actual: e.target.value }).then(cargar);
                    }
                  }}
                />
                {ing.stock_bajo && <span className="stock-bajo-alerta"> ⚠️ repone pronto</span>}
              </td>
              <td>
                <input
                  className="admin-precio-input"
                  type="number"
                  step="0.01"
                  defaultValue={ing.stock_minimo}
                  onBlur={(e) => {
                    if (e.target.value && e.target.value !== ing.stock_minimo) {
                      adminApi.updateIngrediente(ing.id, { stock_minimo: e.target.value }).then(cargar);
                    }
                  }}
                />
              </td>
              <td>
                <button
                  type="button"
                  className="btn-secundario"
                  onClick={() => adminApi.deleteIngrediente(ing.id).then(cargar)}
                >
                  Eliminar
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function PersonalTab() {
  const [usuarios, setUsuarios] = useState<UsuarioStaff[]>([]);
  const [form, setForm] = useState<{ email: string; password: string; rol: Rol }>({
    email: "",
    password: "",
    rol: "mesero",
  });
  const [error, setError] = useState<string | null>(null);

  const cargar = () => adminApi.listUsuarios().then(setUsuarios);
  useEffect(() => {
    cargar();
  }, []);

  const crear = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    if (!form.email.trim() || !form.password.trim()) return;
    try {
      await adminApi.createUsuario({ email: form.email.trim(), password: form.password, rol: form.rol });
      setForm({ email: "", password: "", rol: "mesero" });
      cargar();
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo crear el usuario");
    }
  };

  return (
    <div>
      <form className="admin-form-inline" onSubmit={crear}>
        <input
          type="email"
          placeholder="Correo"
          value={form.email}
          onChange={(e) => setForm({ ...form, email: e.target.value })}
        />
        <input
          type="password"
          placeholder="Contraseña"
          value={form.password}
          onChange={(e) => setForm({ ...form, password: e.target.value })}
        />
        <select value={form.rol} onChange={(e) => setForm({ ...form, rol: e.target.value as Rol })}>
          <option value="mesero">Mesero</option>
          <option value="cajero">Cajero</option>
          <option value="cocina">Cocina</option>
          <option value="admin">Admin</option>
        </select>
        <button type="submit" className="btn-primario">
          Crear usuario
        </button>
      </form>
      {error && <p className="estado-error">{error}</p>}
      <table className="admin-tabla">
        <thead>
          <tr>
            <th>Correo</th>
            <th>Rol</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {usuarios.map((u) => (
            <tr key={u.id}>
              <td>{u.email}</td>
              <td>{ETIQUETA_ROL[u.rol]}</td>
              <td>
                <button
                  type="button"
                  className="btn-secundario"
                  onClick={() => adminApi.deleteUsuario(u.id).then(cargar)}
                >
                  Eliminar
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function SeguridadTab() {
  const [config, setConfig] = useState<RestauranteConfig | null>(null);
  const [pin, setPin] = useState("");
  const [mensaje, setMensaje] = useState<string | null>(null);

  const cargar = () => adminApi.getRestaurante().then(setConfig);
  useEffect(() => {
    cargar();
  }, []);

  const guardar = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!pin.trim()) return;
    await adminApi.setPinCancelacion(pin.trim());
    setPin("");
    setMensaje("Código de cancelación actualizado.");
    cargar();
  };

  return (
    <div>
      <p>
        Código que el personal de cocina debe ingresar para cancelar un pedido. El admin no lo necesita.
        {config && (config.pin_cancelacion_configurado ? " Ya hay un código configurado." : " Aún no hay ningún código configurado.")}
      </p>
      <form className="admin-form-inline" onSubmit={guardar}>
        <input
          type="password"
          placeholder="Nuevo código de cancelación"
          value={pin}
          onChange={(e) => setPin(e.target.value)}
        />
        <button type="submit" className="btn-primario">
          Guardar
        </button>
      </form>
      {mensaje && <p>{mensaje}</p>}
    </div>
  );
}

export function AdminPanel() {
  const { logout } = useAuth();
  const [tab, setTab] = useState<Tab>("categorias");

  return (
    <div className="admin-panel">
      <h2>Panel de administración</h2>
      <nav className="admin-nav">
        <button type="button" className="btn-secundario" onClick={() => setTab("categorias")}>
          Categorías
        </button>
        <button type="button" className="btn-secundario" onClick={() => setTab("items")}>
          Items
        </button>
        <button type="button" className="btn-secundario" onClick={() => setTab("mesas")}>
          Mesas
        </button>
        <button type="button" className="btn-secundario" onClick={() => setTab("ingredientes")}>
          Ingredientes
        </button>
        <button type="button" className="btn-secundario" onClick={() => setTab("personal")}>
          Personal
        </button>
        <button type="button" className="btn-secundario" onClick={() => setTab("seguridad")}>
          Seguridad
        </button>
        <button type="button" className="btn-secundario" onClick={logout} style={{ marginLeft: "auto" }}>
          Cerrar sesión
        </button>
      </nav>
      {tab === "categorias" && <CategoriasTab />}
      {tab === "items" && <ItemsTab />}
      {tab === "personal" && <PersonalTab />}
      {tab === "mesas" && <MesasTab />}
      {tab === "ingredientes" && <IngredientesTab />}
      {tab === "seguridad" && <SeguridadTab />}
    </div>
  );
}
