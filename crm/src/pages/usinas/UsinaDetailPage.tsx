import { useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { usinasApi } from "@/api/usinas";
import { geracaoApi } from "@/api/geracao";
import type { Geracao, GeracaoInput, Usina } from "@/types";
import { useClientesLookup } from "@/hooks/useClientesLookup";
import { Button } from "@/components/ui/Button";
import { IconButton } from "@/components/ui/IconButton";
import { Table, type Column } from "@/components/ui/Table";
import { EmptyState } from "@/components/ui/EmptyState";
import { FullPageSpinner } from "@/components/ui/Spinner";
import { ConfirmDialog } from "@/components/ui/ConfirmDialog";
import { GeracaoForm } from "./GeracaoForm";
import { IconArrowLeft, IconBolt, IconPencil, IconPlus, IconTrash } from "@/components/icons";
import { useToast } from "@/components/ui/ToastProvider";
import { getErrorMessage } from "@/lib/errors";
import { formatCurrency, formatDate, NOMES_MESES } from "@/lib/format";

export function UsinaDetailPage() {
  const { id } = useParams<{ id: string }>();
  const usinaId = Number(id);
  const navigate = useNavigate();
  const { nomeById } = useClientesLookup();
  const { showSuccess, showError } = useToast();

  const [usina, setUsina] = useState<Usina | null>(null);
  const [geracoes, setGeracoes] = useState<Geracao[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);
  const [formTarget, setFormTarget] = useState<Geracao | "new" | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<Geracao | null>(null);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    Promise.all([usinasApi.get(usinaId), usinasApi.listGeracao(usinaId, { per_page: 100 })])
      .then(([usinaRes, geracaoRes]) => {
        if (cancelled) return;
        setUsina(usinaRes);
        setGeracoes(geracaoRes.data);
      })
      .catch((err) => {
        if (!cancelled) setError(getErrorMessage(err));
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [usinaId, reloadKey]);

  const reload = () => setReloadKey((k) => k + 1);

  const porMes = useMemo(() => {
    const mapa = new Map<number, Geracao>();
    for (const g of geracoes) mapa.set(g.mes, g);
    return mapa;
  }, [geracoes]);

  const maxValor = useMemo(() => Math.max(1, ...geracoes.map((g) => g.valor_kwh)), [geracoes]);

  const handleSubmit = async (input: GeracaoInput) => {
    try {
      if (formTarget && formTarget !== "new") {
        await geracaoApi.replace(formTarget.id, input);
        showSuccess("Geração atualizada com sucesso.");
      } else {
        await geracaoApi.create(input);
        showSuccess("Geração registrada com sucesso.");
      }
      setFormTarget(null);
      reload();
    } catch (err) {
      showError(getErrorMessage(err));
      throw err;
    }
  };

  const handleDelete = async () => {
    if (!deleteTarget) return;
    setDeleting(true);
    try {
      await geracaoApi.remove(deleteTarget.id);
      showSuccess("Registro removido.");
      setDeleteTarget(null);
      reload();
    } catch (err) {
      showError(getErrorMessage(err));
    } finally {
      setDeleting(false);
    }
  };

  const columns: Column<Geracao>[] = [
    { key: "ano", header: "Ano", render: (g) => g.ano },
    { key: "mes", header: "Mês", render: (g) => NOMES_MESES[g.mes - 1] },
    { key: "valor_kwh", header: "Geração (kWh)", render: (g) => g.valor_kwh.toLocaleString("pt-BR") },
    {
      key: "acoes",
      header: "",
      className: "text-right",
      render: (g) => (
        <div className="flex justify-end gap-1">
          <IconButton label="Editar" onClick={() => setFormTarget(g)}>
            <IconPencil width={17} height={17} />
          </IconButton>
          <IconButton label="Excluir" tone="danger" onClick={() => setDeleteTarget(g)}>
            <IconTrash width={17} height={17} />
          </IconButton>
        </div>
      ),
    },
  ];

  return (
    <div className="p-6">
      <button
        onClick={() => navigate("/usinas")}
        className="mb-4 inline-flex items-center gap-1.5 text-sm font-medium text-google-blue hover:underline"
      >
        <IconArrowLeft width={16} height={16} />
        Voltar para usinas
      </button>

      {loading ? (
        <FullPageSpinner />
      ) : error || !usina ? (
        <EmptyState icon={<IconBolt width={32} height={32} />} title="Não foi possível carregar a usina" description={error ?? undefined} />
      ) : (
        <>
          <div className="mb-6 flex flex-wrap items-start justify-between gap-4">
            <div>
              <h1 className="text-2xl font-medium text-ink">{usina.nome}</h1>
              <p className="mt-1 text-sm text-ink-secondary">
                Cliente: {nomeById(usina.cliente_id)} · Potência: {usina.potencia_kwp} kWp · Instalação:{" "}
                {formatDate(usina.data_instalacao)} · Investido: {formatCurrency(usina.total_investido)}
              </p>
            </div>
            <Button variant="primary" icon={<IconPlus width={18} height={18} />} onClick={() => setFormTarget("new")}>
              Nova geração
            </Button>
          </div>

          {geracoes.length > 0 && (
            <div className="mb-6 bg-white p-5">
              <p className="mb-4 text-xs font-medium uppercase tracking-wide text-ink-faint">Geração mensal (kWh)</p>
              <div className="flex h-40 items-end gap-2">
                {NOMES_MESES.map((nome, idx) => {
                  const g = porMes.get(idx + 1);
                  const heightPct = g ? Math.max(4, (g.valor_kwh / maxValor) * 100) : 0;
                  return (
                    <div key={nome} className="flex flex-1 flex-col items-center gap-1.5">
                      <div className="flex h-32 w-full items-end">
                        <div
                          className={`w-full rounded-t-md ${g ? "bg-google-blue" : "bg-canvas"}`}
                          style={{ height: `${heightPct}%` }}
                          title={g ? `${nome}: ${g.valor_kwh.toLocaleString("pt-BR")} kWh` : `${nome}: sem registro`}
                        />
                      </div>
                      <span className="text-[10px] text-ink-faint">{nome.slice(0, 3)}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {geracoes.length === 0 ? (
            <EmptyState icon={<IconBolt width={32} height={32} />} title="Nenhum registro de geração" />
          ) : (
            <Table columns={columns} rows={geracoes} rowKey={(g) => g.id} />
          )}
        </>
      )}

      {formTarget && (
        <GeracaoForm
          usinaId={usinaId}
          geracao={formTarget !== "new" ? formTarget : undefined}
          onSubmit={handleSubmit}
          onClose={() => setFormTarget(null)}
        />
      )}

      {deleteTarget && (
        <ConfirmDialog
          title="Excluir geração"
          message={`Remover o registro de ${NOMES_MESES[deleteTarget.mes - 1]}/${deleteTarget.ano}?`}
          busy={deleting}
          onConfirm={handleDelete}
          onCancel={() => setDeleteTarget(null)}
        />
      )}
    </div>
  );
}
