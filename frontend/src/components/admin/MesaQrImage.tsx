import { useEffect, useState } from "react";
import { API_BASE_URL } from "../../api/client";

export function MesaQrImage({ mesaId }: { mesaId: number }) {
  const [url, setUrl] = useState<string | null>(null);

  useEffect(() => {
    let objectUrl: string | null = null;
    const token = localStorage.getItem("access_token");

    fetch(`${API_BASE_URL}/admin/mesas/${mesaId}/qr`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    })
      .then((res) => res.blob())
      .then((blob) => {
        objectUrl = URL.createObjectURL(blob);
        setUrl(objectUrl);
      });

    return () => {
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [mesaId]);

  if (!url) return <span>Cargando QR...</span>;
  return <img src={url} alt={`QR mesa ${mesaId}`} width={120} height={120} />;
}
