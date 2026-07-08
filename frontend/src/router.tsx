import { Routes, Route, Navigate } from "react-router-dom";
import { MenuPage } from "./pages/public/MenuPage";
import { CheckoutPage } from "./pages/public/CheckoutPage";
import { OrderStatusPage } from "./pages/public/OrderStatusPage";
import { LoginPage } from "./pages/staff/LoginPage";
import { KitchenScreen } from "./pages/staff/KitchenScreen";
import { AdminPanel } from "./pages/staff/AdminPanel";
import { NotFoundPage } from "./pages/NotFoundPage";
import { RequireAuth } from "./components/RequireAuth";

export function AppRouter() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/login" replace />} />
      <Route path="/r/:slug/mesa/:codigoQr" element={<MenuPage />} />
      <Route path="/r/:slug/checkout" element={<CheckoutPage />} />
      <Route path="/r/:slug/pedido/:pedidoId" element={<OrderStatusPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/cocina"
        element={
          <RequireAuth roles={["admin", "cocina"]}>
            <KitchenScreen />
          </RequireAuth>
        }
      />
      <Route
        path="/admin/*"
        element={
          <RequireAuth roles={["admin"]}>
            <AdminPanel />
          </RequireAuth>
        }
      />
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
}
