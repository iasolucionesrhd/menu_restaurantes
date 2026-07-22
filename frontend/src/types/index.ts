export interface ModificadorMenu {
  id: number;
  nombre: string;
  precio_extra: string;
}

export interface ModificadorGrupoMenu {
  id: number;
  nombre: string;
  obligatorio: boolean;
  seleccion_multiple: boolean;
  modificadores: ModificadorMenu[];
}

export interface ItemMenu {
  id: number;
  nombre: string;
  descripcion: string | null;
  precio: string;
  imagen_url: string | null;
  modificador_grupos: ModificadorGrupoMenu[];
}

export interface CategoriaMenu {
  id: number;
  nombre: string;
  items: ItemMenu[];
}

export interface MenuPublico {
  restaurante_nombre: string;
  restaurante_slug: string;
  payment_mode: "stub" | "tilopay";
  categorias: CategoriaMenu[];
}

export interface MesaPublica {
  numero: number | null;
  tipo_entrega: "mesa" | "retiro";
}

export interface CartItemModificador {
  modificadorId: number;
  nombre: string;
  precioExtra: string;
}

export interface CartItem {
  itemId: number;
  nombre: string;
  precioUnitario: string;
  cantidad: number;
  notas?: string;
  modificadores?: CartItemModificador[];
}

export type MetodoPago = "tarjeta" | "sinpe" | "apple_pay" | "efectivo_en_restaurante";

export type EstadoPedido = "recibido" | "en_cocina" | "listo" | "entregado" | "cancelado";

export interface ItemPedidoModificador {
  nombre: string;
  precio_extra: string;
}

export interface ItemPedido {
  id: number;
  item_id: number;
  nombre: string;
  cantidad: number;
  precio_unitario: string;
  notas: string | null;
  modificadores: ItemPedidoModificador[];
}

export interface Pedido {
  id: number;
  estado: EstadoPedido;
  metodo_pago: MetodoPago;
  monto_total: string;
  tipo_entrega: "mesa" | "retiro";
  mesa_numero: number | null;
  cliente_nombre: string;
  creado_en: string;
  en_cocina_en: string | null;
  listo_en: string | null;
  requiere_factura: boolean;
  items: ItemPedido[];
}

export type Rol = "admin" | "cocina";

export interface Usuario {
  id: number;
  email: string;
  rol: Rol;
  restaurante_id: number;
  restaurante_slug: string;
}
