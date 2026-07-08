import { useEffect, useState } from "react";
import { useAuth } from "../../context/AuthContext";
import { adminApi, type Categoria, type Item, type Mesa } from "../../api/admin";
import { MesaQrImage } from "../../components/admin/MesaQrImage";

type Tab = "categorias" | "items" | "mesas";

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

function ItemsTab() {
  const [items, setItems] = useState<Item[]>([]);
  const [categorias, setCategorias] = useState<Categoria[]>([]);
  const [form, setForm] = useState({ nombre: "", precio: "", categoria_id: "" });

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
            <th></th>
          </tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr key={item.id}>
              <td>{item.nombre}</td>
              <td>{item.precio}</td>
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
                  onClick={() => adminApi.deleteItem(item.id).then(cargar)}
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
        <button type="button" className="btn-secundario" onClick={logout} style={{ marginLeft: "auto" }}>
          Cerrar sesión
        </button>
      </nav>
      {tab === "categorias" && <CategoriasTab />}
      {tab === "items" && <ItemsTab />}
      {tab === "mesas" && <MesasTab />}
    </div>
  );
}
