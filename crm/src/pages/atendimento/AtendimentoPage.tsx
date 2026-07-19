import { useState } from "react";
import { indicacoesApi } from "@/api/indicacoes";
import { usePaginatedResource } from "@/hooks/usePaginatedResource";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Select, Textarea } from "@/components/ui/Field";
import { EmptyState } from "@/components/ui/EmptyState";
import { FullPageSpinner } from "@/components/ui/Spinner";
import { Pagination } from "@/components/ui/Pagination";
import { useToast } from "@/components/ui/ToastProvider";
import { getErrorMessage } from "@/lib/errors";
import { formatCurrency, formatDateTime } from "@/lib/format";
import { IconAlertCircle, IconCornerUpRight, IconMessageCircle } from "@/components/icons";
import { EncerrarAtendimentoModal, type EncerrarAtendimentoInput } from "./EncerrarAtendimentoModal";
import { setores } from "./types";
import type { Indicacao, StatusIndicacao } from "@/types";

const statusBadge: Record<StatusIndicacao, { tone: "yellow" | "blue" | "gray" | "green" | "red"; label: string }> = {
  recebido: { tone: "yellow", label: "Recebido" },
  em_atendimento: { tone: "blue", label: "Em andamento" },
  negociacao: { tone: "blue", label: "Negociação" },
  fechado: { tone: "green", label: "Fechado" },
  perdido: { tone: "red", label: "Perdido" },
  cancelado: { tone: "gray", label: "Cancelado" },
};

const nivelInteresseLabel: Record<Indicacao["nivel_interesse"], string> = {
  sim: "Interessado",
  talvez: "Talvez",
  nao_sei: "Não sabe ainda",
};

const filtros: { value: StatusIndicacao | "todos"; label: string }[] = [
  { value: "todos", label: "Todos" },
  { value: "recebido", label: "Recebidos" },
  { value: "em_atendimento", label: "Em andamento" },
  { value: "negociacao", label: "Negociação" },
  { value: "fechado", label: "Fechados" },
  { value: "perdido", label: "Perdidos" },
  { value: "cancelado", label: "Cancelados" },
];

const ENCERRADOS: StatusIndicacao[] = ["fechado", "perdido", "cancelado"];

export function AtendimentoPage() {
  const { showSuccess, showError } = useToast();
  const [filtro, setFiltro] = useState<StatusIndicacao | "todos">("todos");
  const [selecionadoId, setSelecionadoId] = useState<number | null>(null);
  const [setorSelecionado, setSetorSelecionado] = useState(setores[0]);
  const [observacoesDraft, setObservacoesDraft] = useState("");
  const [salvando, setSalvando] = useState(false);
  const [mostrarEncerrar, setMostrarEncerrar] = useState(false);

  const fila = usePaginatedResource<Indicacao>(
    indicacoesApi.list,
    filtro === "todos" ? {} : { status: filtro },
  );

  const selecionado = fila.data.find((a) => a.id === selecionadoId) ?? null;

  const selecionar = (a: Indicacao) => {
    setSelecionadoId(a.id);
    setSetorSelecionado(a.setor ?? setores[0]);
    setObservacoesDraft(a.observacoes ?? "");
  };

  const atualizarSelecionado = async (input: Parameters<typeof indicacoesApi.update>[1], mensagemSucesso: string) => {
    if (!selecionado) return;
    try {
      await indicacoesApi.update(selecionado.id, input);
      showSuccess(mensagemSucesso);
      fila.reload();
    } catch (err) {
      showError(getErrorMessage(err));
    }
  };

  const handleAssumir = () => atualizarSelecionado({ status: "em_atendimento" }, "Atendimento assumido.");

  const handleTransferir = () => atualizarSelecionado({ setor: setorSelecionado }, `Transferido para ${setorSelecionado}.`);

  const handleSalvarObservacoes = async () => {
    if (!selecionado) return;
    setSalvando(true);
    try {
      await indicacoesApi.update(selecionado.id, { observacoes: observacoesDraft });
      showSuccess("Observações salvas.");
      fila.reload();
    } catch (err) {
      showError(getErrorMessage(err));
    } finally {
      setSalvando(false);
    }
  };

  const resultadoParaStatus: Record<EncerrarAtendimentoInput["resultado"], StatusIndicacao> = {
    novo_contrato: "fechado",
    em_andamento: "negociacao",
    sem_interesse: "perdido",
    cancelado: "cancelado",
  };

  const handleEncerrar = async (input: EncerrarAtendimentoInput) => {
    if (!selecionado) return;
    try {
      await indicacoesApi.update(selecionado.id, {
        status: resultadoParaStatus[input.resultado],
        resultado: input.resultado,
        valor_sistema: input.valor_sistema,
        tipo_contrato: input.tipo_contrato,
        observacoes: input.observacoes,
      });
      showSuccess(`Atendimento de ${selecionado.nome_indicado} atualizado.`);
      setMostrarEncerrar(false);
      fila.reload();
    } catch (err) {
      showError(getErrorMessage(err));
    }
  };

  return (
    <>
      <div className="grid h-[calc(100vh-4rem)] grid-cols-1 lg:grid-cols-[360px_1fr]">
        <div className="flex flex-col border-r border-border bg-white">
          <div className="flex gap-1 overflow-x-auto border-b border-border p-2">
            {filtros.map((f) => (
              <button
                key={f.value}
                onClick={() => setFiltro(f.value)}
                className={`shrink-0 px-3 py-1.5 text-xs font-medium transition-colors ${
                  filtro === f.value ? "bg-google-blue-bg text-google-blue-dark" : "text-ink-secondary hover:bg-canvas"
                }`}
              >
                {f.label}
              </button>
            ))}
          </div>

          {fila.loading ? (
            <FullPageSpinner />
          ) : fila.error ? (
            <div className="p-4">
              <EmptyState icon={<IconAlertCircle width={28} height={28} />} title="Não foi possível carregar a fila" description={fila.error} />
            </div>
          ) : fila.data.length === 0 ? (
            <div className="p-4">
              <EmptyState
                icon={<IconAlertCircle width={28} height={28} />}
                title="Nenhum atendimento na fila"
                description="Assim que um parceiro cadastrar uma indicação no app, ela aparece aqui automaticamente."
              />
            </div>
          ) : (
            <>
              <ul className="flex-1 overflow-y-auto">
                {fila.data.map((a) => (
                  <li key={a.id}>
                    <button
                      onClick={() => selecionar(a)}
                      className={`w-full border-b border-border px-4 py-3 text-left transition-colors hover:bg-canvas ${
                        selecionadoId === a.id ? "bg-google-blue-bg/40" : ""
                      }`}
                    >
                      <div className="flex items-center justify-between gap-2">
                        <span className="font-medium text-ink">{a.nome_indicado}</span>
                        <Badge tone={statusBadge[a.status].tone}>{statusBadge[a.status].label}</Badge>
                      </div>
                      <p className="mt-1 text-xs text-ink-secondary">Indicado por {a.indicador_nome ?? "—"}</p>
                      <p className="text-xs text-ink-faint">{a.setor ?? "Sem setor"}</p>
                    </button>
                  </li>
                ))}
              </ul>
              {fila.pagination && <Pagination pagination={fila.pagination} onPageChange={fila.setPage} />}
            </>
          )}
        </div>

        <div className="flex flex-col overflow-y-auto bg-white">
          {!selecionado ? (
            <div className="flex flex-1 items-center justify-center">
              <EmptyState
                icon={<IconMessageCircle width={28} height={28} />}
                title="Selecione um atendimento"
                description="Escolha uma indicação na lista ao lado para ver os detalhes."
              />
            </div>
          ) : (
            <>
              <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border px-5 py-4">
                <div>
                  <p className="font-medium text-ink">{selecionado.nome_indicado}</p>
                  <p className="text-xs text-ink-secondary">
                    {selecionado.telefone_indicado} · Indicado por {selecionado.indicador_nome ?? "—"} ({selecionado.indicador_codigo ?? "—"})
                  </p>
                </div>
                <div className="flex flex-wrap items-center gap-2">
                  {selecionado.status === "recebido" && (
                    <Button variant="secondary" onClick={handleAssumir}>
                      Assumir atendimento
                    </Button>
                  )}
                  <div className="w-44">
                    <Select
                      label=""
                      aria-label="Transferir para setor"
                      value={setorSelecionado}
                      onChange={(e) => setSetorSelecionado(e.target.value)}
                      disabled={ENCERRADOS.includes(selecionado.status)}
                      className="py-2"
                    >
                      {setores.map((s) => (
                        <option key={s} value={s}>
                          {s}
                        </option>
                      ))}
                    </Select>
                  </div>
                  <Button
                    variant="secondary"
                    icon={<IconCornerUpRight width={16} height={16} />}
                    disabled={ENCERRADOS.includes(selecionado.status)}
                    onClick={handleTransferir}
                  >
                    Transferir
                  </Button>
                  <Button
                    variant="danger"
                    disabled={ENCERRADOS.includes(selecionado.status)}
                    onClick={() => setMostrarEncerrar(true)}
                  >
                    Encerrar atendimento
                  </Button>
                </div>
              </div>

              <div className="flex-1 space-y-6 px-5 py-4">
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                  <div>
                    <p className="text-xs font-medium text-ink-faint">Cidade</p>
                    <p className="text-sm text-ink">{selecionado.cidade ?? "—"}</p>
                  </div>
                  <div>
                    <p className="text-xs font-medium text-ink-faint">Conta de energia estimada</p>
                    <p className="text-sm text-ink">{formatCurrency(selecionado.conta_energia_estimada)}</p>
                  </div>
                  <div>
                    <p className="text-xs font-medium text-ink-faint">Nível de interesse</p>
                    <p className="text-sm text-ink">{nivelInteresseLabel[selecionado.nivel_interesse]}</p>
                  </div>
                  <div>
                    <p className="text-xs font-medium text-ink-faint">Recebido em</p>
                    <p className="text-sm text-ink">{formatDateTime(selecionado.criado_em)}</p>
                  </div>
                  {ENCERRADOS.includes(selecionado.status) && (
                    <>
                      <div>
                        <p className="text-xs font-medium text-ink-faint">Resultado</p>
                        <p className="text-sm text-ink">{selecionado.resultado ?? "—"}</p>
                      </div>
                      {selecionado.status === "fechado" && (
                        <>
                          <div>
                            <p className="text-xs font-medium text-ink-faint">Valor do sistema</p>
                            <p className="text-sm text-ink">{formatCurrency(selecionado.valor_sistema)}</p>
                          </div>
                          <div>
                            <p className="text-xs font-medium text-ink-faint">Comissão gerada</p>
                            <p className="text-sm text-ink">{formatCurrency(selecionado.comissao_gerada)}</p>
                          </div>
                        </>
                      )}
                    </>
                  )}
                </div>

                <div className="max-w-xl">
                  <Textarea
                    label="Observações"
                    rows={5}
                    placeholder="O que foi conversado, próximos passos, dados relevantes..."
                    value={observacoesDraft}
                    onChange={(e) => setObservacoesDraft(e.target.value)}
                    disabled={ENCERRADOS.includes(selecionado.status)}
                  />
                  {!ENCERRADOS.includes(selecionado.status) && (
                    <Button
                      variant="secondary"
                      className="mt-2"
                      disabled={salvando || observacoesDraft === (selecionado.observacoes ?? "")}
                      onClick={handleSalvarObservacoes}
                    >
                      Salvar observações
                    </Button>
                  )}
                </div>
              </div>
            </>
          )}
        </div>
      </div>

      {mostrarEncerrar && selecionado && (
        <EncerrarAtendimentoModal
          clienteNome={selecionado.nome_indicado}
          onClose={() => setMostrarEncerrar(false)}
          onSubmit={handleEncerrar}
        />
      )}
    </>
  );
}
