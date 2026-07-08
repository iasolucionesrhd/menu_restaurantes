import { createContext, useContext, useState, type ReactNode } from "react";
import type { Usuario } from "../types";
import { login as loginRequest } from "../api/auth";

interface AuthContextValue {
  usuario: Usuario | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
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

  return <AuthContext.Provider value={{ usuario, login, logout }}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth debe usarse dentro de AuthProvider");
  return ctx;
}
