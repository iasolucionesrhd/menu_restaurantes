import { useEffect, useRef } from "react";
import type { ClienteInput } from "../../api/pedidos";
import { GoogleSignInButton } from "./GoogleSignInButton";
import { obtenerPerfilCliente } from "../../api/clientes";
import { ApiError } from "../../api/client";

interface Props {
  slug: string;
  value: ClienteInput;
  onChange: (value: ClienteInput) => void;
}

export function CustomerForm({ slug, value, onChange }: Props) {
  // El callback de Google resuelve la búsqueda de perfil de forma
  // asíncrona; para evitar mezclar con un estado ya viejo si el usuario
  // edita algo mientras tanto, la continuación lee el valor más reciente
  // desde esta ref en vez del `value` capturado en el closure original.
  const valorActualRef = useRef(value);
  useEffect(() => {
    valorActualRef.current = value;
  }, [value]);

  const handleGoogleSignIn = ({
    nombre,
    correo,
    googleIdToken,
  }: {
    nombre: string;
    correo: string;
    googleIdToken: string;
  }) => {
    onChange({
      ...value,
      nombre: nombre || value.nombre,
      correo: correo || value.correo,
      google_id_token: googleIdToken,
    });

    obtenerPerfilCliente(slug, googleIdToken)
      .then((perfil) => {
        const actual = valorActualRef.current;
        const tieneFactura = Boolean(perfil.factura_nombre || perfil.factura_cedula || perfil.factura_direccion);
        onChange({
          ...actual,
          // El nombre guardado en el perfil gana sobre el del JWT: refleja
          // lo que el cliente corrigió manualmente en un pedido anterior.
          nombre: perfil.nombre || actual.nombre,
          correo: perfil.correo ?? actual.correo,
          telefono: perfil.telefono ?? actual.telefono,
          google_id_token: googleIdToken,
          ...(tieneFactura
            ? {
                datos_facturacion: {
                  nombre: perfil.factura_nombre ?? "",
                  cedula: perfil.factura_cedula ?? "",
                  correo: perfil.factura_correo ?? undefined,
                  telefono: perfil.factura_telefono ?? undefined,
                  direccion: perfil.factura_direccion ?? "",
                  actividad_economica: perfil.factura_actividad_economica ?? undefined,
                },
              }
            : {}),
        });
      })
      .catch((err) => {
        // 404 = todavía no hay perfil guardado para esta cuenta, no es un error real.
        if (!(err instanceof ApiError && err.status === 404)) {
          console.error("No se pudo cargar el perfil guardado", err);
        }
      });
  };

  const datosFacturacion = value.datos_facturacion;

  return (
    <>
      <GoogleSignInButton onSignIn={handleGoogleSignIn} />
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
        Correo (opcional)
        <input
          type="email"
          value={value.correo ?? ""}
          onChange={(e) => onChange({ ...value, correo: e.target.value })}
        />
      </label>
      <label>
        Teléfono (opcional)
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
      <label style={{ flexDirection: "row", alignItems: "center", gap: "8px" }}>
        <input
          type="checkbox"
          checked={value.consentimiento_marketing}
          onChange={(e) => onChange({ ...value, consentimiento_marketing: e.target.checked })}
        />
        Quiero recibir promociones y novedades por correo o teléfono (opcional)
      </label>
      <label style={{ flexDirection: "row", alignItems: "center", gap: "8px" }}>
        <input
          type="checkbox"
          checked={datosFacturacion !== undefined}
          onChange={(e) =>
            onChange({
              ...value,
              datos_facturacion: e.target.checked
                ? (datosFacturacion ?? { nombre: "", cedula: "", direccion: "" })
                : undefined,
            })
          }
        />
        Necesito factura
      </label>
      {datosFacturacion && (
        <div className="factura-form">
          <label>
            Nombre completo o razón social
            <input
              type="text"
              required
              value={datosFacturacion.nombre}
              onChange={(e) =>
                onChange({ ...value, datos_facturacion: { ...datosFacturacion, nombre: e.target.value } })
              }
            />
          </label>
          <label>
            Cédula
            <input
              type="text"
              required
              value={datosFacturacion.cedula}
              onChange={(e) =>
                onChange({ ...value, datos_facturacion: { ...datosFacturacion, cedula: e.target.value } })
              }
            />
          </label>
          <label>
            Correo para factura (opcional)
            <input
              type="email"
              value={datosFacturacion.correo ?? ""}
              onChange={(e) =>
                onChange({ ...value, datos_facturacion: { ...datosFacturacion, correo: e.target.value } })
              }
            />
          </label>
          <label>
            Teléfono para factura (opcional)
            <input
              type="tel"
              value={datosFacturacion.telefono ?? ""}
              onChange={(e) =>
                onChange({ ...value, datos_facturacion: { ...datosFacturacion, telefono: e.target.value } })
              }
            />
          </label>
          <label>
            Ubicación
            <input
              type="text"
              required
              value={datosFacturacion.direccion}
              onChange={(e) =>
                onChange({ ...value, datos_facturacion: { ...datosFacturacion, direccion: e.target.value } })
              }
            />
          </label>
          <label>
            Código de actividad económica (opcional)
            <input
              type="text"
              value={datosFacturacion.actividad_economica ?? ""}
              onChange={(e) =>
                onChange({
                  ...value,
                  datos_facturacion: { ...datosFacturacion, actividad_economica: e.target.value },
                })
              }
            />
          </label>
        </div>
      )}
    </>
  );
}
