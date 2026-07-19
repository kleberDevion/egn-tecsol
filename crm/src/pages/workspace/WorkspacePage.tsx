import { Navigate, useParams } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { FullPageSpinner } from "@/components/ui/Spinner";
import { IconBuilding, IconChart, IconLink, IconZap } from "@/components/icons";
import type { GrupoChave } from "@/types";

const WORKSPACES: Record<string, { nome: string; icon: typeof IconChart; descricao: string }> = {
  financeiro: {
    nome: "Financeiro",
    icon: IconChart,
    descricao: "Espaço da equipe financeira.",
  },
  marketing: {
    nome: "Marketing",
    icon: IconLink,
    descricao: "Espaço da equipe de marketing e mídias sociais.",
  },
  tecnologia: {
    nome: "Tecnologia",
    icon: IconZap,
    descricao: "Espaço da equipe de tecnologia/desenvolvimento.",
  },
  diretoria: {
    nome: "CEO / Diretoria",
    icon: IconBuilding,
    descricao: "Espaço da diretoria.",
  },
};

export function WorkspacePage() {
  const { grupo } = useParams<{ grupo: string }>();
  const { user, loading } = useAuth();

  if (loading) return <FullPageSpinner />;
  if (!user) return <Navigate to="/login" replace />;

  const config = grupo ? WORKSPACES[grupo] : undefined;
  if (!config) return <Navigate to="/" replace />;

  const autorizado = user.papel === "admin" || user.grupos.includes(grupo as GrupoChave);
  if (!autorizado) return <Navigate to="/" replace />;

  const Icon = config.icon;

  return (
    <div className="p-6">
      <div className="flex items-center gap-3">
        <span className="inline-flex h-10 w-10 items-center justify-center bg-google-blue-bg text-google-blue">
          <Icon width={20} height={20} />
        </span>
        <div>
          <h1 className="text-lg font-medium text-ink">Workspace: {config.nome}</h1>
          <p className="text-sm text-ink-secondary">{config.descricao}</p>
        </div>
      </div>

      <div className="mt-8 bg-white p-8 text-center">
        <p className="text-sm text-ink-secondary">
          Ainda não há ferramentas específicas configuradas para este grupo.
        </p>
        <p className="mt-1 text-xs text-ink-faint">
          Fale com um administrador pra priorizar o que deve entrar aqui primeiro.
        </p>
      </div>
    </div>
  );
}
