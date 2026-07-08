import type { CategoriaMenu } from "../../types";
import { ItemCard } from "./ItemCard";

export function CategoryList({ categorias }: { categorias: CategoriaMenu[] }) {
  return (
    <div className="category-list">
      {categorias.map((categoria) => (
        <section key={categoria.id} className="categoria-seccion">
          <h3>{categoria.nombre}</h3>
          {categoria.items.length === 0 ? (
            <p className="categoria-vacia">Sin items disponibles.</p>
          ) : (
            <div className="items-grid">
              {categoria.items.map((item) => (
                <ItemCard key={item.id} item={item} />
              ))}
            </div>
          )}
        </section>
      ))}
    </div>
  );
}
