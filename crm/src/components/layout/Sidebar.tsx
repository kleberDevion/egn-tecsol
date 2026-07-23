import { NavLink } from "react-router-dom";
import type { ReactElement, SVGProps } from "react";
import {
  IconBolt,
  IconBuilding,
  IconChart,
  IconChevronLeft,
  IconChevronRight,
  IconFolder,
  IconHelpCircle,
  IconHome,
  IconLink,
  IconShield,
  IconUsers,
  IconX,
  IconZap,
} from "@/components/icons";
import { useAuth } from "@/contexts/AuthContext";
import { useSidebar } from "@/contexts/SidebarContext";
import type { GrupoChave } from "@/types";

type Item = {
  to: string;
  label: string;
  icon: (p: SVGProps<SVGSVGElement>) => ReactElement;
  end?: boolean;
};

const navItems: Item[] = [
  { to: "/", label: "Início", icon: IconHome, end: true },
  { to: "/clientes", label: "Clientes", icon: IconUsers },
  { to: "/projetos", label: "Projetos", icon: IconFolder },
  { to: "/usinas", label: "Usinas", icon: IconBolt },
  { to: "/concessionarias", label: "Concessionárias", icon: IconBuilding },
];

const suporteItem: Item = { to: "/suporte", label: "Suporte", icon: IconHelpCircle };
const documentosItem: Item = { to: "/geracao-documentos", label: "Geração de Documentação", icon: IconFolder };
const indicacoesItem: Item = { to: "/indicacoes", label: "Indicações", icon: IconChart };

const WORKSPACE_ITEMS: Partial<Record<GrupoChave, Item>> = {
  financeiro: { to: "/workspace/financeiro", label: "Financeiro", icon: IconChart },
  marketing: { to: "/workspace/marketing", label: "Marketing", icon: IconLink },
  tecnologia: { to: "/workspace/tecnologia", label: "Tecnologia", icon: IconZap },
  diretoria: { to: "/workspace/diretoria", label: "Diretoria", icon: IconBuilding },
};

function useItens(): Item[] {
  const { user } = useAuth();
  if (user?.papel === "admin") {
    return [
      ...navItems,
      { to: "/admin", label: "Administração", icon: IconShield },
      indicacoesItem,
      documentosItem,
      suporteItem,
    ];
  }
  const grupoItems = (user?.grupos ?? [])
    .filter((g) => g === "vendas" || g in WORKSPACE_ITEMS)
    .map((g) => (g === "vendas" ? indicacoesItem : WORKSPACE_ITEMS[g]!));
  return [...navItems, ...grupoItems, documentosItem, suporteItem];
}

function Link({ item, compacto, onClick }: { item: Item; compacto: boolean; onClick?: () => void }) {
  const { to, label, icon: Icon, end } = item;
  return (
    <NavLink
      to={to}
      end={end}
      onClick={onClick}
      title={compacto ? label : undefined}
      className={({ isActive }) =>
        `flex items-center gap-3 py-2.5 text-sm font-medium transition-colors ${
          compacto ? "justify-center px-0" : "px-6"
        } ${isActive ? "bg-google-blue-bg text-google-blue-dark" : "text-ink-secondary hover:bg-canvas"}`
      }
    >
      <Icon width={20} height={20} className="shrink-0" />
      {!compacto && <span className="truncate">{label}</span>}
    </NavLink>
  );
}

export function Sidebar() {
  const itens = useItens();
  const { colapsada, alternar, mobileAberta, fecharMobile } = useSidebar();

  return (
    <>
      {/* Desktop: barra fixa, colapsavel */}
      <aside
        className={`fixed left-0 top-16 hidden h-[calc(100vh-4rem)] shrink-0 flex-col overflow-y-auto overflow-x-hidden border-r border-border bg-white py-2 transition-[width] duration-200 md:flex ${
          colapsada ? "w-16" : "w-64"
        }`}
      >
        <nav className="flex flex-1 flex-col">
          {itens.map((item) => (
            <Link key={item.to} item={item} compacto={colapsada} />
          ))}
        </nav>

        <button
          onClick={alternar}
          title={colapsada ? "Expandir menu" : "Recolher menu"}
          aria-label={colapsada ? "Expandir menu" : "Recolher menu"}
          className={`flex items-center gap-3 border-t border-border py-2.5 text-sm text-ink-secondary transition-colors hover:bg-canvas ${
            colapsada ? "justify-center px-0" : "px-6"
          }`}
        >
          {colapsada ? (
            <IconChevronRight width={20} height={20} className="shrink-0" />
          ) : (
            <>
              <IconChevronLeft width={20} height={20} className="shrink-0" />
              <span className="truncate">Recolher</span>
            </>
          )}
        </button>
      </aside>

      {/* Mobile: gaveta por cima do conteudo */}
      {mobileAberta && (
        <div className="fixed inset-0 z-30 md:hidden">
          <div
            className="absolute inset-0 bg-black/40"
            onClick={fecharMobile}
            role="presentation"
          />
          <aside className="absolute left-0 top-0 flex h-full w-72 max-w-[80%] flex-col overflow-y-auto bg-white py-2 shadow-lg">
            <div className="flex items-center justify-between px-4 pb-2">
              <span className="text-sm font-medium text-ink">Menu</span>
              <button
                onClick={fecharMobile}
                aria-label="Fechar menu"
                className="p-1 text-ink-secondary hover:text-ink"
              >
                <IconX width={20} height={20} />
              </button>
            </div>
            <nav className="flex flex-col">
              {itens.map((item) => (
                <Link key={item.to} item={item} compacto={false} onClick={fecharMobile} />
              ))}
            </nav>
          </aside>
        </div>
      )}
    </>
  );
}
