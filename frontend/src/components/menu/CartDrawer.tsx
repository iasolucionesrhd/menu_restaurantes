import { useNavigate } from "react-router-dom";
import { useCart } from "../../context/CartContext";
import { formatMoney } from "../../utils/format";

export function CartDrawer({ restauranteSlug }: { restauranteSlug: string }) {
  const { state, updateCantidad, removeItem, total } = useCart();

  const navigate = useNavigate();

  if (state.items.length === 0) {
    return (
      <aside className="cart-drawer cart-drawer-vacio">
        <p>Tu carrito está vacío.</p>
      </aside>
    );
  }

  return (
    <aside className="cart-drawer">
      <h3>Tu pedido</h3>
      <ul className="cart-items">
        {state.items.map((item) => (
          <li key={`${item.itemId}-${item.notas ?? ""}`} className="cart-item">
            <div>
              <span className="cart-item-nombre">{item.nombre}</span>
              {item.notas && <span className="cart-item-notas"> ({item.notas})</span>}
            </div>
            <div className="cart-item-controles">
              <button type="button" onClick={() => updateCantidad(item.itemId, item.cantidad - 1)}>
                -
              </button>
              <span>{item.cantidad}</span>
              <button type="button" onClick={() => updateCantidad(item.itemId, item.cantidad + 1)}>
                +
              </button>
              <span className="cart-item-subtotal">
                {formatMoney(Number(item.precioUnitario) * item.cantidad)}
              </span>
              <button type="button" className="btn-quitar" onClick={() => removeItem(item.itemId)}>
                ✕
              </button>
            </div>
          </li>
        ))}
      </ul>
      <div className="cart-total">
        <strong>Total: {formatMoney(total)}</strong>
      </div>
      <button
        type="button"
        className="btn-primario btn-checkout"
        onClick={() => navigate(`/r/${restauranteSlug}/checkout`)}
      >
        Ir a checkout
      </button>
    </aside>
  );
}
