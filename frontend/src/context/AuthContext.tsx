import { createContext, useContext, useState, type ReactNode } from "react";
import type { Usuario } from "../types";
import { login as loginRequest, cambiarRestaurante } from "../api/auth";

interface AuthContextValue {
  usuario: Usuario | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  cambiarSucursal: (restauranteId: number) => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

function loadUsuario(): Usuario | null {
  const raw = localStorage.getItem("usuario");
  return raw ? (JSON.parse(raw) as Usuario) : null;
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [usuario, setUsuario] = useState<Usuario | null>(loadUsuario);

  const login = async (email: string, password: string) => {
    const { access_token, usuario: u } = await loginRequest(email, password);
    localStorage.setItem("access_token", access_token);
    localStorage.setItem("usuario", JSON.stringify(u));
    setUsuario(u);
  };

  const logout = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("usuario");
    setUsuario(null);
  };

  const cambiarSucursal = async (restauranteId: number) => {
    const { access_token, usuario: u } = await cambiarRestaurante(restauranteId);
    localStorage.setItem("access_token", access_token);
    localStorage.setItem("usuario", JSON.stringify(u));
    setUsuario(u);
  };

  return (
    <AuthContext.Provider value={{ usuario, login, logout, cambiarSucursal }}>{children}</AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth debe usarse dentro de AuthProvider");
  return ctx;
}
