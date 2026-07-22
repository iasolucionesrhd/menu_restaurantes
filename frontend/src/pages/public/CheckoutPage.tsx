import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { useCart, claveLineaCarrito } from "../../context/CartContext";
import { getMenuPublico } from "../../api/menu";
import { crearPedido, type ClienteInput } from "../../api/pedidos";
import { CustomerForm } from "../../components/checkout/CustomerForm";
import { PaymentMethodSelector } from "../../components/checkout/PaymentMethodSelector";
import { StubPaymentPanel } from "../../components/checkout/StubPaymentPanel";
import { ApiError } from "../../api/client";
import type { MetodoPago } from "../../types";
import { formatMoney } from "../../utils/format";

export function CheckoutPage() {
  const { slug } = useParams<{ slug: string }>();
  const { state, total, clear } = useCart();
  const navigate = useNavigate();

  const menuQuery = useQuery({
    queryKey: ["menu", slug],
    queryFn: () => getMenuPublico(slug!),
    enabled: !!slug,
  });

  const [cliente, setCliente] = useState<ClienteInput>({
    nombre: "",
    correo: "",
    telefono: "",
    consentimiento_datos: true,
    consentimiento_marketing: false,
  });
  const [metodoPago, setMetodoPago] = useState<MetodoPago>("efectivo_en_restaurante");
  const [enviando, setEnviando] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!slug || state.items.length === 0) {
    return (
      <div className="checkout-page">
        <p className="estado-error">Tu carrito está vacío.</p>
      </div>
    );
  }

  const finalizarPedido = async (paymentIntentId?: string) => {
    setEnviando(true);
    setError(null);
    try {
      const pedido = await crearPedido(slug, {
        mesaCodigoQr: state.mesaCodigoQr,
        cliente,
        metodoPago,
        items: state.items,
        paymentIntentId,
      });
      clear();
      navigate(`/r/${slug}/pedido/${pedido.id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudo crear el pedido");
    } finally {
      setEnviando(false);
    }
  };

  const handleSubmitEfectivo = async (e: React.FormEvent) => {
    e.preventDefault();
    await finalizarPedido();
  };

  const esPagoOnline = metodoPago !== "efectivo_en_restaurante";
  const paymentMode = menuQuery.data?.payment_mode ?? "stub";
  const datosFacturacion = cliente.datos_facturacion;
  const facturaIncompleta =
    datosFacturacion !== undefined &&
    (!datosFacturacion.nombre.trim() || !datosFacturacion.cedula.trim() || !datosFacturacion.direccion.trim());

  return (
    <div className="checkout-page">
      <h2>Checkout</h2>
      <div className="checkout-resumen">
        {state.items.map((item) => {
          const extras = (item.modificadores ?? []).reduce((acc, m) => acc + Number(m.precioExtra), 0);
          return (
            <div key={claveLineaCarrito(item)}>
              {item.cantidad}× {item.nombre}
              {item.modificadores && item.modificadores.length > 0
                ? ` (${item.modificadores.map((m) => m.nombre).join(", ")})`
                : ""}
              {" — "}
              {formatMoney((Number(item.precioUnitario) + extras) * item.cantidad)}
            </div>
          );
        })}
        <p>
          <strong>Total: {formatMoney(total)}</strong>
        </p>
      </div>

      <form className="checkout-form" onSubmit={handleSubmitEfectivo}>
        <CustomerForm slug={slug} value={cliente} onChange={setCliente} />

        <h3>Método de pago</h3>
        <PaymentMethodSelector value={metodoPago} onChange={setMetodoPago} />

        {error && <p className="estado-error">{error}</p>}

        {esPagoOnline ? (
          paymentMode === "stub" ? (
            <StubPaymentPanel
              slug={slug}
              monto={total}
              metodoPago={metodoPago}
              onAprobado={(paymentIntentId) => finalizarPedido(paymentIntentId)}
            />
          ) : (
            <p className="estado-error">
              El pago con Tilopay en vivo aún no está configurado para este restaurante.
            </p>
          )
        ) : (
          <button type="submit" className="btn-primario" disabled={enviando || !cliente.nombre || facturaIncompleta}>
            {enviando ? "Enviando..." : "Confirmar pedido"}
          </button>
        )}
      </form>
    </div>
  );
}
