import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { clientesApi } from "@/api/clientes";
import { projetosApi } from "@/api/projetos";
import { usinasApi } from "@/api/usinas";
import { concessionariasApi } from "@/api/concessionarias";
import { dashboardApi } from "@/api/dashboard";
import { Table, type Column } from "@/components/ui/Table";
import { Pagination } from "@/components/ui/Pagination";
import {
  IconActivity,
  IconBolt,
  IconBuilding,
  IconCheckCircle,
  IconFolder,
  IconLogout,
  IconPencil,
  IconPlus,
  IconTrash,
  IconUsers,
  IconX,
} from "@/components/icons";
import { FullPageSpinner } from "@/components/ui/Spinner";
import { usePaginatedResource } from "@/hooks/usePaginatedResource";
import { acaoLabel, entidadeLabel } from "@/lib/activity";
import { formatDateTime } from "@/lib/format";
import type { ActivityLogEntry, AvaliacoesSuporteResumo, MinhasMetricas } from "@/types";

interface Stat {
  label: string;
  to: string;
  icon: typeof IconUsers;
  value: number | null;
  tone: string;
}

const acaoIcons: Record<string, typeof IconPlus> = {
  create: IconPlus,
  update: IconPencil,
  delete: IconTrash,
  login: IconLogout,
  logout: IconLogout,
  change_password: IconActivity,
};

export function DashboardPage() {
  const [stats, setStats] = useState<Stat[]>([
    { label: "Clientes", to: "/clientes", icon: IconUsers, value: null, tone: "bg-google-blue-bg text-google-blue" },
    { label: "Projetos", to: "/projetos", icon: IconFolder, value: null, tone: "bg-google-green-bg text-google-green" },
    { label: "Usinas", to: "/usinas", icon: IconBolt, value: null, tone: "bg-yellow-50 text-google-yellow" },
    { label: "Concessionárias", to: "/concessionarias", icon: IconBuilding, value: null, tone: "bg-google-red-bg text-google-red" },
  ]);
  const [loading, setLoading] = useState(true);
  const [metricas, setMetricas] = useState<MinhasMetricas | null>(null);
  const [avaliacoes, setAvaliacoes] = useState<AvaliacoesSuporteResumo | null>(null);

  useEffect(() => {
    Promise.all([
      clientesApi.list({ per_page: 1 }),
      projetosApi.list({ per_page: 1 }),
      usinasApi.list({ per_page: 1 }),
      concessionariasApi.list({ per_page: 1 }),
    ])
      .then(([clientes, projetos, usinas, concessionarias]) => {
        setStats((prev) => [
          { ...prev[0], value: clientes.pagination.total_items },
          { ...prev[1], value: projetos.pagination.total_items },
          { ...prev[2], value: usinas.pagination.total_items },
          { ...prev[3], value: concessionarias.pagination.total_items },
        ]);
      })
      .finally(() => setLoading(false));

    dashboardApi.minhasMetricas().then(setMetricas);
    dashboardApi.avaliacoesSuporte().then(setAvaliacoes);
  }, []);

  const atividade = usePaginatedResource<ActivityLogEntry>(dashboardApi.minhaAtividade);

  const columns: Column<ActivityLogEntry>[] = [
    {
      key: "acao",
      header: "Ação",
      render: (row) => {
        const Icon = acaoIcons[row.acao] ?? IconActivity;
        return (
          <span className="inline-flex items-center gap-2">
            <Icon width={16} height={16} className="text-ink-faint" />
            {acaoLabel(row.acao)}
          </span>
        );
      },
    },
    { key: "entidade", header: "Área", render: (row) => entidadeLabel(row.entidade) },
    { key: "descricao", header: "Descrição", render: (row) => row.descricao ?? "—" },
    { key: "criado_em", header: "Quando", render: (row) => formatDateTime(row.criado_em) },
  ];

  return (
    <div className="p-6">
      {loading ? (
        <FullPageSpinner />
      ) : (
        <div className="grid grid-cols-1 gap-px bg-border sm:grid-cols-2 lg:grid-cols-4">
          {stats.map(({ label, to, icon: Icon, value, tone }) => (
            <Link key={label} to={to} className="bg-white p-5 transition-colors hover:bg-canvas">
              <span className={`inline-flex h-10 w-10 items-center justify-center ${tone}`}>
                <Icon width={20} height={20} />
              </span>
              <p className="mt-4 text-3xl font-medium text-ink">{value}</p>
              <p className="text-sm text-ink-secondary">{label}</p>
            </Link>
          ))}
        </div>
      )}

      <h2 className="mb-4 mt-10 text-lg font-medium text-ink">Minha atividade</h2>

      {metricas && (
        <div className="mb-6 grid grid-cols-2 gap-px bg-border sm:grid-cols-4">
          <div className="bg-white p-4">
            <p className="text-2xl font-medium text-ink">{metricas.criacoes}</p>
            <p className="text-xs text-ink-secondary">Criações</p>
          </div>
          <div className="bg-white p-4">
            <p className="text-2xl font-medium text-ink">{metricas.edicoes}</p>
            <p className="text-xs text-ink-secondary">Edições</p>
          </div>
          <div className="bg-white p-4">
            <p className="text-2xl font-medium text-ink">{metricas.exclusoes}</p>
            <p className="text-xs text-ink-secondary">Exclusões</p>
          </div>
          <div className="bg-white p-4">
            <p className="text-sm font-medium text-ink">{formatDateTime(metricas.ultimo_login_em)}</p>
            <p className="text-xs text-ink-secondary">Último login</p>
          </div>
        </div>
      )}

      {avaliacoes && avaliacoes.total > 0 && (
        <>
          <h2 className="mb-4 mt-10 text-lg font-medium text-ink">Avaliações do suporte</h2>
          <div className="mb-6 grid grid-cols-3 gap-px bg-border">
            <div className="bg-white p-4">
              <p className="text-2xl font-medium text-ink">{avaliacoes.total}</p>
              <p className="text-xs text-ink-secondary">Avaliações no total</p>
            </div>
            <div className="bg-white p-4">
              <p className="inline-flex items-center gap-1.5 text-2xl font-medium text-google-green">
                <IconCheckCircle width={18} height={18} />
                {avaliacoes.positivas}
              </p>
              <p className="text-xs text-ink-secondary">Positivas</p>
            </div>
            <div className="bg-white p-4">
              <p className="inline-flex items-center gap-1.5 text-2xl font-medium text-google-red">
                <IconX width={18} height={18} />
                {avaliacoes.negativas}
              </p>
              <p className="text-xs text-ink-secondary">Negativas</p>
            </div>
          </div>
        </>
      )}

      {atividade.loading ? (
        <FullPageSpinner />
      ) : atividade.data.length === 0 ? (
        <p className="text-sm text-ink-secondary">Nenhuma atividade registrada ainda.</p>
      ) : (
        <>
          <Table columns={columns} rows={atividade.data} rowKey={(row) => row.id} />
          {atividade.pagination && (
            <Pagination pagination={atividade.pagination} onPageChange={atividade.setPage} />
          )}
        </>
      )}
    </div>
  );
}
