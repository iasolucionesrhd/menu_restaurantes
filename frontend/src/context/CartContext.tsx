import { createContext, useCallback, useContext, useEffect, useMemo, useReducer, type ReactNode } from "react";
import type { CartItem } from "../types";

interface CartState {
  restauranteSlug: string | null;
  mesaCodigoQr: string | null;
  tipoEntrega: "mesa" | "retiro" | null;
  items: CartItem[];
}

type CartAction =
  | { type: "SET_CONTEXTO"; restauranteSlug: string; mesaCodigoQr: string; tipoEntrega: "mesa" | "retiro" }
  | { type: "ADD_ITEM"; item: CartItem }
  | { type: "UPDATE_CANTIDAD"; clave: string; cantidad: number }
  | { type: "REMOVE_ITEM"; clave: string }
  | { type: "CLEAR" };

const STORAGE_KEY = "menu-digital-cart";

const initialState: CartState = {
  restauranteSlug: null,
  mesaCodigoQr: null,
  tipoEntrega: null,
  items: [],
};

// Dos líneas del carrito son "la misma" solo si coinciden item, notas Y el
// mismo conjunto de modificadores elegidos — Pizza Grande y Pizza Chica no
// deben sumarse en una sola línea.
export function claveLineaCarrito(item: Pick<CartItem, "itemId" | "notas" | "modificadores">): string {
  const modKey = (item.modificadores ?? [])
    .map((m) => m.modificadorId)
    .sort((a, b) => a - b)
    .join(",");
  return `${item.itemId}|${item.notas ?? ""}|${modKey}`;
}

function loadInitialState(): CartState {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    if (raw) return JSON.parse(raw) as CartState;
  } catch {
    // ignora datos corruptos
  }
  return initialState;
}

function reducer(state: CartState, action: CartAction): CartState {
  switch (action.type) {
    case "SET_CONTEXTO": {
      if (state.restauranteSlug !== action.restauranteSlug) {
        return {
          restauranteSlug: action.restauranteSlug,
          mesaCodigoQr: action.mesaCodigoQr,
          tipoEntrega: action.tipoEntrega,
          items: [],
        };
      }
      if (state.mesaCodigoQr === action.mesaCodigoQr && state.tipoEntrega === action.tipoEntrega) {
        return state;
      }
      return { ...state, mesaCodigoQr: action.mesaCodigoQr, tipoEntrega: action.tipoEntrega };
    }
    case "ADD_ITEM": {
      const claveNueva = claveLineaCarrito(action.item);
      const existente = state.items.find((i) => claveLineaCarrito(i) === claveNueva);
      if (existente) {
        return {
          ...state,
          items: state.items.map((i) =>
            i === existente ? { ...i, cantidad: i.cantidad + action.item.cantidad } : i
          ),
        };
      }
      return { ...state, items: [...state.items, action.item] };
    }
    case "UPDATE_CANTIDAD":
      return {
        ...state,
        items:
          action.cantidad <= 0
            ? state.items.filter((i) => claveLineaCarrito(i) !== action.clave)
            : state.items.map((i) => (claveLineaCarrito(i) === action.clave ? { ...i, cantidad: action.cantidad } : i)),
      };
    case "REMOVE_ITEM":
      return { ...state, items: state.items.filter((i) => claveLineaCarrito(i) !== action.clave) };
    case "CLEAR":
      return { ...state, items: [] };
    default:
      return state;
  }
}

function subtotalItem(item: CartItem): number {
  const extras = (item.modificadores ?? []).reduce((acc, m) => acc + Number(m.precioExtra), 0);
  return (Number(item.precioUnitario) + extras) * item.cantidad;
}

interface CartContextValue {
  state: CartState;
  setContexto: (restauranteSlug: string, mesaCodigoQr: string, tipoEntrega: "mesa" | "retiro") => void;
  addItem: (item: CartItem) => void;
  updateCantidad: (clave: string, cantidad: number) => void;
  removeItem: (clave: string) => void;
  clear: () => void;
  total: number;
}

const CartContext = createContext<CartContextValue | null>(null);

export function CartProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(reducer, undefined, loadInitialState);

  useEffect(() => {
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  }, [state]);

  const total = useMemo(() => state.items.reduce((acc, i) => acc + subtotalItem(i), 0), [state.items]);

  const setContexto = useCallback(
    (restauranteSlug: string, mesaCodigoQr: string, tipoEntrega: "mesa" | "retiro") =>
      dispatch({ type: "SET_CONTEXTO", restauranteSlug, mesaCodigoQr, tipoEntrega }),
    []
  );
  const addItem = useCallback((item: CartItem) => dispatch({ type: "ADD_ITEM", item }), []);
  const updateCantidad = useCallback(
    (clave: string, cantidad: number) => dispatch({ type: "UPDATE_CANTIDAD", clave, cantidad }),
    []
  );
  const removeItem = useCallback((clave: string) => dispatch({ type: "REMOVE_ITEM", clave }), []);
  const clear = useCallback(() => dispatch({ type: "CLEAR" }), []);

  const value: CartContextValue = useMemo(
    () => ({ state, setContexto, addItem, updateCantidad, removeItem, clear, total }),
    [state, setContexto, addItem, updateCantidad, removeItem, clear, total]
  );

  return <CartContext.Provider value={value}>{children}</CartContext.Provider>;
}

export function useCart(): CartContextValue {
  const ctx = useContext(CartContext);
  if (!ctx) throw new Error("useCart debe usarse dentro de CartProvider");
  return ctx;
}
