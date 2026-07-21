import { NavLink } from "react-router-dom";
import {
  IconBolt,
  IconBuilding,
  IconChart,
  IconFolder,
  IconHelpCircle,
  IconHome,
  IconLink,
  IconShield,
  IconUsers,
  IconZap,
} from "@/components/icons";
import { useAuth } from "@/contexts/AuthContext";
import type { GrupoChave } from "@/types";

const navItems = [
  { to: "/", label: "Início", icon: IconHome, end: true },
  { to: "/clientes", label: "Clientes", icon: IconUsers },
  { to: "/projetos", label: "Projetos", icon: IconFolder },
  { to: "/usinas", label: "Usinas", icon: IconBolt },
  { to: "/concessionarias", label: "Concessionárias", icon: IconBuilding },
];

const suporteItem = { to: "/suporte", label: "Suporte", icon: IconHelpCircle, end: false };
const indicacoesItem = { to: "/indicacoes", label: "Indicações", icon: IconChart, end: false };

const WORKSPACE_ITEMS: Partial<
  Record<GrupoChave, { to: string; label: string; icon: typeof IconChart; end: boolean }>
> = {
  financeiro: { to: "/workspace/financeiro", label: "Financeiro", icon: IconChart, end: false },
  marketing: { to: "/workspace/marketing", label: "Marketing", icon: IconLink, end: false },
  tecnologia: { to: "/workspace/tecnologia", label: "Tecnologia", icon: IconZap, end: false },
  diretoria: { to: "/workspace/diretoria", label: "Diretoria", icon: IconBuilding, end: false },
};

export function Sidebar() {
  const { user } = useAuth();

  const items = (() => {
    if (user?.papel === "admin") {
      return [
        ...navItems,
        { to: "/admin", label: "Administração", icon: IconShield },
        indicacoesItem,
        suporteItem,
      ];
    }

    const grupoItems = (user?.grupos ?? [])
      .filter((g) => g === "vendas" || g in WORKSPACE_ITEMS)
      .map((g) => (g === "vendas" ? indicacoesItem : WORKSPACE_ITEMS[g]!));

    return [...navItems, ...grupoItems, suporteItem];
  })();

  return (
    <aside className="fixed left-0 top-16 hidden h-[calc(100vh-4rem)] w-64 shrink-0 overflow-y-auto border-r border-border bg-white py-2 md:block">
      <nav className="flex flex-col">
        {items.map(({ to, label, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              `flex items-center gap-3 px-6 py-2.5 text-sm font-medium transition-colors ${
                isActive
                  ? "bg-google-blue-bg text-google-blue-dark"
                  : "text-ink-secondary hover:bg-canvas"
              }`
            }
          >
            <Icon width={20} height={20} />
            {label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
