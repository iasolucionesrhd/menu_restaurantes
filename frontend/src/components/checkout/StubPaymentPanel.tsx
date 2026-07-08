import { useState } from "react";
import { confirmarPago, iniciarPago } from "../../api/pagos";
import type { MetodoPago } from "../../types";

interface Props {
  slug: string;
  monto: number;
  metodoPago: MetodoPago;
  onAprobado: (paymentIntentId: string) => void;
}

export function StubPaymentPanel({ slug, monto, metodoPago, onAprobado }: Props) {
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const simularPago = async () => {
    setCargando(true);
    setError(null);
    try {
      const intent = await iniciarPago(slug, monto.toFixed(2), metodoPago, `checkout-${Date.now()}`);
      const confirmacion = await confirmarPago(slug, intent.payment_intent_id);
      if (!confirmacion.aprobado) {
        setError("El pago simulado fue rechazado.");
        return;
      }
      onAprobado(intent.payment_intent_id);
    } catch {
      setError("No se pudo procesar el pago simulado.");
    } finally {
      setCargando(false);
    }
  };

  return (
    <div className="stub-payment-panel">
      <p>Modo de prueba: este pago se simula, no se cobra dinero real.</p>
      {error && <p className="estado-error">{error}</p>}
      <button type="button" className="btn-primario" onClick={simularPago} disabled={cargando}>
        {cargando ? "Procesando..." : "Simular pago aprobado"}
      </button>
    </div>
  );
}
