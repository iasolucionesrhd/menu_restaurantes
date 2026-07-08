import { useEffect, useRef, useState } from "react";
import type { EstadoPedido, Pedido } from "../types";

const WS_BASE_URL = import.meta.env.VITE_WS_BASE_URL ?? "ws://localhost:8000/api/ws";

type Mensaje =
  | { tipo: "nuevo_pedido"; pedido: Pedido }
  | { tipo: "estado_actualizado"; pedido_id: number; estado: EstadoPedido };

interface Callbacks {
  onNuevoPedido: (pedido: Pedido) => void;
  onEstadoActualizado: (pedidoId: number, estado: EstadoPedido) => void;
}

export function useKitchenSocket(slug: string | undefined, callbacks: Callbacks) {
  const [conectado, setConectado] = useState(false);
  const callbacksRef = useRef(callbacks);
  callbacksRef.current = callbacks;

  useEffect(() => {
    if (!slug) return;

    let socket: WebSocket | null = null;
    let reintentoTimeout: ReturnType<typeof setTimeout> | null = null;
    let cerradoManualmente = false;

    const conectar = () => {
      const token = localStorage.getItem("access_token");
      socket = new WebSocket(`${WS_BASE_URL}/cocina/${slug}?token=${token ?? ""}`);

      socket.onopen = () => setConectado(true);

      socket.onmessage = (event) => {
        const mensaje = JSON.parse(event.data) as Mensaje;
        if (mensaje.tipo === "nuevo_pedido") {
          callbacksRef.current.onNuevoPedido(mensaje.pedido);
        } else if (mensaje.tipo === "estado_actualizado") {
          callbacksRef.current.onEstadoActualizado(mensaje.pedido_id, mensaje.estado);
        }
      };

      socket.onclose = () => {
        setConectado(false);
        if (!cerradoManualmente) {
          reintentoTimeout = setTimeout(conectar, 3000);
        }
      };
    };

    conectar();

    return () => {
      cerradoManualmente = true;
      if (reintentoTimeout) clearTimeout(reintentoTimeout);
      socket?.close();
    };
  }, [slug]);

  return { conectado };
}
