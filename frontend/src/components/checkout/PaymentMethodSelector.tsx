import { useEffect, useState } from "react";
import type { MetodoPago } from "../../types";

interface Props {
  value: MetodoPago;
  onChange: (metodo: MetodoPago) => void;
}

export function PaymentMethodSelector({ value, onChange }: Props) {
  const [applePayDisponible, setApplePayDisponible] = useState(false);

  useEffect(() => {
    const win = window as unknown as { ApplePaySession?: { canMakePayments: () => boolean } };
    setApplePayDisponible(Boolean(win.ApplePaySession?.canMakePayments()));
  }, []);

  const opciones: { valor: MetodoPago; etiqueta: string }[] = [
    { valor: "tarjeta", etiqueta: "Tarjeta" },
    { valor: "sinpe", etiqueta: "SINPE Móvil" },
    ...(applePayDisponible ? [{ valor: "apple_pay" as MetodoPago, etiqueta: "Apple Pay" }] : []),
    { valor: "efectivo_en_restaurante", etiqueta: "Efectivo en el restaurante" },
  ];

  return (
    <div className="metodo-pago-opciones">
      {opciones.map((op) => (
        <label key={op.valor}>
          <input
            type="radio"
            name="metodo_pago"
            value={op.valor}
            checked={value === op.valor}
            onChange={() => onChange(op.valor)}
          />
          {op.etiqueta}
        </label>
      ))}
    </div>
  );
}
