import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from "react";
import { authApi } from "@/api/auth";
import { ApiError } from "@/api/client";
import { connectSocket, disconnectSocket } from "@/lib/socket";
import type { LoginInput, SetupInput, Usuario } from "@/types";

interface AuthContextValue {
  user: Usuario | null;
  loading: boolean;
  login: (input: LoginInput) => Promise<void>;
  setup: (input: SetupInput) => Promise<void>;
  logout: () => Promise<void>;
  refresh: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<Usuario | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    try {
      const me = await authApi.me();
      setUser(me);
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        setUser(null);
      } else {
        throw err;
      }
    }
  }, []);

  useEffect(() => {
    refresh().finally(() => setLoading(false));
  }, [refresh]);

  useEffect(() => {
    if (user) {
      connectSocket();
    } else {
      disconnectSocket();
    }
  }, [user]);

  const login = useCallback(async (input: LoginInput) => {
    const loggedUser = await authApi.login(input);
    setUser(loggedUser);
  }, []);

  const setup = useCallback(async (input: SetupInput) => {
    const createdUser = await authApi.setup(input);
    setUser(createdUser);
  }, []);

  const logout = useCallback(async () => {
    await authApi.logout();
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, loading, login, setup, logout, refresh }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth deve ser usado dentro de AuthProvider");
  return ctx;
}
