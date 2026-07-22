import { useState } from "react";
import type { ItemMenu } from "../../types";
import { formatMoney } from "../../utils/format";
import { useCart } from "../../context/CartContext";

export function ItemCard({ item }: { item: ItemMenu }) {
  const { addItem } = useCart();
  const [notas, setNotas] = useState("");
  const [expandido, setExpandido] = useState(false);
  const [seleccion, setSeleccion] = useState<Record<number, number[]>>({});

  const grupos = item.modificador_grupos;

  const elegirUnica = (grupoId: number, modificadorId: number) => {
    setSeleccion({ ...seleccion, [grupoId]: [modificadorId] });
  };

  const alternarMultiple = (grupoId: number, modificadorId: number) => {
    const actuales = seleccion[grupoId] ?? [];
    setSeleccion({
      ...seleccion,
      [grupoId]: actuales.includes(modificadorId)
        ? actuales.filter((id) => id !== modificadorId)
        : [...actuales, modificadorId],
    });
  };

  const grupoIncompleto = grupos.find((g) => g.obligatorio && (seleccion[g.id] ?? []).length === 0);

  const modificadoresElegidos = grupos.flatMap((g) =>
    (seleccion[g.id] ?? []).map((id) => g.modificadores.find((m) => m.id === id)!)
  );
  const extraTotal = modificadoresElegidos.reduce((acc, m) => acc + Number(m.precio_extra), 0);

  const handleAgregar = () => {
    if (grupoIncompleto) return;
    addItem({
      itemId: item.id,
      nombre: item.nombre,
      precioUnitario: item.precio,
      cantidad: 1,
      notas: notas.trim() || undefined,
      modificadores: modificadoresElegidos.map((m) => ({
        modificadorId: m.id,
        nombre: m.nombre,
        precioExtra: m.precio_extra,
      })),
    });
    setNotas("");
    setSeleccion({});
    setExpandido(false);
  };

  return (
    <div className="item-card">
      <div className="item-card-info">
        <h4>{item.nombre}</h4>
        {item.descripcion && <p className="item-descripcion">{item.descripcion}</p>}
        <span className="item-precio">{formatMoney(Number(item.precio) + extraTotal)}</span>
      </div>
      {grupos.map((grupo) => (
        <div key={grupo.id} className="modificador-grupo">
          <strong>
            {grupo.nombre}
            {grupo.obligatorio && <span className="modificador-obligatorio"> (obligatorio)</span>}
          </strong>
          {grupo.modificadores.map((mod) => {
            const marcado = (seleccion[grupo.id] ?? []).includes(mod.id);
            return (
              <label key={mod.id} className="modificador-opcion">
                <input
                  type={grupo.seleccion_multiple ? "checkbox" : "radio"}
                  name={`grupo-${grupo.id}-${item.id}`}
                  checked={marcado}
                  onChange={() =>
                    grupo.seleccion_multiple ? alternarMultiple(grupo.id, mod.id) : elegirUnica(grupo.id, mod.id)
                  }
                />
                {mod.nombre}
                {Number(mod.precio_extra) > 0 && ` (+${formatMoney(mod.precio_extra)})`}
              </label>
            );
          })}
        </div>
      ))}
      {expandido && (
        <input
          type="text"
          placeholder="Notas (ej. sin cebolla)"
          value={notas}
          onChange={(e) => setNotas(e.target.value)}
          className="item-notas-input"
        />
      )}
      <div className="item-card-acciones">
        {!expandido && (
          <button type="button" onClick={() => setExpandido(true)} className="btn-secundario">
            Notas
          </button>
        )}
        <button type="button" onClick={handleAgregar} className="btn-primario" disabled={!!grupoIncompleto}>
          Agregar
        </button>
      </div>
    </div>
  );
}
