import { useEffect, useState } from "react";
import { indicacoesApi } from "@/api/indicacoes";
import { Table, type Column } from "@/components/ui/Table";
import { Badge } from "@/components/ui/Badge";
import { EmptyState } from "@/components/ui/EmptyState";
import { FullPageSpinner } from "@/components/ui/Spinner";
import { formatCurrency } from "@/lib/format";
import { getErrorMessage } from "@/lib/errors";
import { IconAlertCircle, IconBolt, IconChart, IconMessageCircle, IconUsers } from "@/components/icons";
import type { ResumoIndicador } from "@/types";

const resumoColumns: Column<ResumoIndicador>[] = [
  { key: "nome", header: "Indicador", render: (r) => `${r.nome} · ${r.codigo_indicacao}` },
  { key: "nivel", header: "Nível", render: (r) => <Badge tone="blue">{r.nivel}</Badge> },
  { key: "total_indicacoes", header: "Indicações", render: (r) => r.total_indicacoes },
  {
    key: "em_andamento",
    header: "Em andamento",
    render: (r) => (r.em_andamento > 0 ? <Badge tone="yellow">{r.em_andamento}</Badge> : "—"),
  },
  {
    key: "fechados",
    header: "Contratos fechados",
    render: (r) => (r.fechados > 0 ? <Badge tone="green">{r.fechados}</Badge> : "—"),
  },
  {
    key: "cancelados",
    header: "Cancelados/perdidos",
    render: (r) => (r.cancelados > 0 ? <Badge tone="red">{r.cancelados}</Badge> : "—"),
  },
  { key: "total_ganhos", header: "Total ganho", render: (r) => formatCurrency(r.total_ganhos) },
];

export function IndicacoesPage() {
  const [resumo, setResumo] = useState<ResumoIndicador[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    indicacoesApi
      .resumo()
      .then((res) => setResumo(res.data))
      .catch((err) => setError(getErrorMessage(err)));
  }, []);

  const totalIndicadores = resumo?.length ?? 0;
  const totalIndicacoes = resumo?.reduce((sum, r) => sum + r.total_indicacoes, 0) ?? 0;
  const totalEmAndamento = resumo?.reduce((sum, r) => sum + r.em_andamento, 0) ?? 0;
  const totalFechados = resumo?.reduce((sum, r) => sum + r.fechados, 0) ?? 0;

  const stats = [
    { label: "Parceiros indicadores", value: totalIndicadores, icon: IconUsers, tone: "bg-google-blue-bg text-google-blue" },
    { label: "Indicações recebidas", value: totalIndicacoes, icon: IconChart, tone: "bg-google-green-bg text-google-green" },
    { label: "Atendimentos em andamento", value: totalEmAndamento, icon: IconMessageCircle, tone: "bg-yellow-50 text-google-yellow" },
    { label: "Contratos fechados", value: totalFechados, icon: IconBolt, tone: "bg-google-red-bg text-google-red" },
  ];

  return (
    <div className="p-6">
      <div className="grid grid-cols-1 gap-px bg-border sm:grid-cols-2 lg:grid-cols-4">
        {stats.map(({ label, value, icon: Icon, tone }) => (
          <div key={label} className="bg-white p-5">
            <span className={`inline-flex h-10 w-10 items-center justify-center ${tone}`}>
              <Icon width={20} height={20} />
            </span>
            <p className="mt-4 text-3xl font-medium text-ink">{resumo ? value : "—"}</p>
            <p className="text-sm text-ink-secondary">{label}</p>
          </div>
        ))}
      </div>

      <h2 className="mb-4 mt-10 text-lg font-medium text-ink">Desempenho por indicador</h2>

      {!resumo ? (
        <FullPageSpinner />
      ) : error ? (
        <EmptyState icon={<IconAlertCircle width={32} height={32} />} title="Não foi possível carregar os dados de indicação" description={error} />
      ) : resumo.length === 0 ? (
        <EmptyState
          icon={<IconAlertCircle width={32} height={32} />}
          title="Nenhum indicador cadastrado ainda"
          description="Assim que parceiros se cadastrarem no app de indicações e começarem a gerar leads, este painel mostra o desempenho e o saldo de comissão de cada um."
        />
      ) : (
        <Table columns={resumoColumns} rows={resumo} rowKey={(r) => r.id} />
      )}
    </div>
  );
}
