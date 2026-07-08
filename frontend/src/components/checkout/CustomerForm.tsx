import type { ClienteInput } from "../../api/pedidos";

interface Props {
  value: ClienteInput;
  onChange: (value: ClienteInput) => void;
}

export function CustomerForm({ value, onChange }: Props) {
  return (
    <>
      <label>
        Nombre
        <input
          type="text"
          required
          value={value.nombre}
          onChange={(e) => onChange({ ...value, nombre: e.target.value })}
        />
      </label>
      <label>
        Correo
        <input
          type="email"
          value={value.correo ?? ""}
          onChange={(e) => onChange({ ...value, correo: e.target.value })}
        />
      </label>
      <label>
        Teléfono
        <input
          type="tel"
          value={value.telefono ?? ""}
          onChange={(e) => onChange({ ...value, telefono: e.target.value })}
        />
      </label>
      <label style={{ flexDirection: "row", alignItems: "center", gap: "8px" }}>
        <input
          type="checkbox"
          checked={value.consentimiento_datos}
          onChange={(e) => onChange({ ...value, consentimiento_datos: e.target.checked })}
        />
        Autorizo el uso de mis datos de contacto según la Ley 8968 de protección de datos
      </label>
    </>
  );
}
