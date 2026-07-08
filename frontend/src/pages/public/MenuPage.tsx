import { useEffect } from "react";
import { useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { getMenuPublico, getMesaPublica } from "../../api/menu";
import { CategoryList } from "../../components/menu/CategoryList";
import { CartDrawer } from "../../components/menu/CartDrawer";
import { useCart } from "../../context/CartContext";

export function MenuPage() {
  const { slug, codigoQr } = useParams<{ slug: string; codigoQr: string }>();
  const { setContexto } = useCart();

  const menuQuery = useQuery({
    queryKey: ["menu", slug],
    queryFn: () => getMenuPublico(slug!),
    enabled: !!slug,
  });

  const mesaQuery = useQuery({
    queryKey: ["mesa", slug, codigoQr],
    queryFn: () => getMesaPublica(slug!, codigoQr!),
    enabled: !!slug && !!codigoQr,
  });

  useEffect(() => {
    if (slug && codigoQr && mesaQuery.data) {
      setContexto(slug, codigoQr, mesaQuery.data.tipo_entrega);
    }
  }, [slug, codigoQr, mesaQuery.data, setContexto]);

  if (menuQuery.isLoading || mesaQuery.isLoading) {
    return <p className="estado-carga">Cargando menú...</p>;
  }

  if (menuQuery.isError || !menuQuery.data) {
    return <p className="estado-error">No se pudo cargar el menú. Verifica el enlace del QR.</p>;
  }

  if (mesaQuery.isError) {
    return <p className="estado-error">Esta mesa no es válida para este restaurante.</p>;
  }

  const mesa = mesaQuery.data;

  return (
    <div className="menu-page">
      <header className="menu-header">
        <h1>{menuQuery.data.restaurante_nombre}</h1>
        {mesa && (
          <p className="menu-subtitulo">
            {mesa.tipo_entrega === "mesa" ? `Mesa ${mesa.numero}` : "Para retirar"}
          </p>
        )}
      </header>
      <div className="menu-contenido">
        <CategoryList categorias={menuQuery.data.categorias} />
        <CartDrawer restauranteSlug={slug!} />
      </div>
    </div>
  );
}
