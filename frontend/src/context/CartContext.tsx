import { createContext, useContext, useEffect, useMemo, useReducer, type ReactNode } from "react";
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
  | { type: "UPDATE_CANTIDAD"; itemId: number; cantidad: number }
  | { type: "REMOVE_ITEM"; itemId: number }
  | { type: "CLEAR" };

const STORAGE_KEY = "menu-digital-cart";

const initialState: CartState = {
  restauranteSlug: null,
  mesaCodigoQr: null,
  tipoEntrega: null,
  items: [],
};

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
      return { ...state, mesaCodigoQr: action.mesaCodigoQr, tipoEntrega: action.tipoEntrega };
    }
    case "ADD_ITEM": {
      const existente = state.items.find(
        (i) => i.itemId === action.item.itemId && i.notas === action.item.notas
      );
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
            ? state.items.filter((i) => i.itemId !== action.itemId)
            : state.items.map((i) => (i.itemId === action.itemId ? { ...i, cantidad: action.cantidad } : i)),
      };
    case "REMOVE_ITEM":
      return { ...state, items: state.items.filter((i) => i.itemId !== action.itemId) };
    case "CLEAR":
      return { ...state, items: [] };
    default:
      return state;
  }
}

interface CartContextValue {
  state: CartState;
  setContexto: (restauranteSlug: string, mesaCodigoQr: string, tipoEntrega: "mesa" | "retiro") => void;
  addItem: (item: CartItem) => void;
  updateCantidad: (itemId: number, cantidad: number) => void;
  removeItem: (itemId: number) => void;
  clear: () => void;
  total: number;
}

const CartContext = createContext<CartContextValue | null>(null);

export function CartProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(reducer, undefined, loadInitialState);

  useEffect(() => {
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  }, [state]);

  const total = useMemo(
    () => state.items.reduce((acc, i) => acc + Number(i.precioUnitario) * i.cantidad, 0),
    [state.items]
  );

  const value: CartContextValue = {
    state,
    setContexto: (restauranteSlug, mesaCodigoQr, tipoEntrega) =>
      dispatch({ type: "SET_CONTEXTO", restauranteSlug, mesaCodigoQr, tipoEntrega }),
    addItem: (item) => dispatch({ type: "ADD_ITEM", item }),
    updateCantidad: (itemId, cantidad) => dispatch({ type: "UPDATE_CANTIDAD", itemId, cantidad }),
    removeItem: (itemId) => dispatch({ type: "REMOVE_ITEM", itemId }),
    clear: () => dispatch({ type: "CLEAR" }),
    total,
  };

  return <CartContext.Provider value={value}>{children}</CartContext.Provider>;
}

export function useCart(): CartContextValue {
  const ctx = useContext(CartContext);
  if (!ctx) throw new Error("useCart debe usarse dentro de CartProvider");
  return ctx;
}
