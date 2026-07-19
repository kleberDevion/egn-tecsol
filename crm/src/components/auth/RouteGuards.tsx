import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { FullPageSpinner } from "@/components/ui/Spinner";
import type { GrupoChave } from "@/types";

export function RequireAuth() {
  const { user, loading } = useAuth();

  if (loading) return <FullPageSpinner />;
  if (!user) return <Navigate to="/login" replace />;
  return <Outlet />;
}

export function RequireAdmin() {
  const { user, loading } = useAuth();

  if (loading) return <FullPageSpinner />;
  if (!user) return <Navigate to="/login" replace />;
  if (user.papel !== "admin") return <Navigate to="/" replace />;
  return <Outlet />;
}

/** Libera acesso pra admin (sempre) ou usuários que pertencem ao grupo informado. */
export function RequireGrupo({ grupo }: { grupo: GrupoChave }) {
  const { user, loading } = useAuth();

  if (loading) return <FullPageSpinner />;
  if (!user) return <Navigate to="/login" replace />;
  if (user.papel !== "admin" && !user.grupos.includes(grupo)) return <Navigate to="/" replace />;
  return <Outlet />;
}
