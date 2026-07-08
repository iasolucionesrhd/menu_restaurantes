import { useState } from "react";
import type { ItemMenu } from "../../types";
import { formatMoney } from "../../utils/format";
import { useCart } from "../../context/CartContext";

export function ItemCard({ item }: { item: ItemMenu }) {
  const { addItem } = useCart();
  const [notas, setNotas] = useState("");
  const [expandido, setExpandido] = useState(false);

  const handleAgregar = () => {
    addItem({
      itemId: item.id,
      nombre: item.nombre,
      precioUnitario: item.precio,
      cantidad: 1,
      notas: notas.trim() || undefined,
    });
    setNotas("");
    setExpandido(false);
  };

  return (
    <div className="item-card">
      <div className="item-card-info">
        <h4>{item.nombre}</h4>
        {item.descripcion && <p className="item-descripcion">{item.descripcion}</p>}
        <span className="item-precio">{formatMoney(item.precio)}</span>
      </div>
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
        <button type="button" onClick={handleAgregar} className="btn-primario">
          Agregar
        </button>
      </div>
    </div>
  );
}
