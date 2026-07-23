import { useCallback, useEffect, useRef, useState } from "react";
import { geracaoDocumentosApi } from "@/api/geracaoDocumentos";
import { Button } from "@/components/ui/Button";
import { IconFile, IconRefresh } from "@/components/icons";
import { Badge } from "@/components/ui/Badge";
import { Modal } from "@/components/ui/Modal";
import { Input } from "@/components/ui/Field";
import { FullPageSpinner } from "@/components/ui/Spinner";
import { useToast } from "@/components/ui/ToastProvider";
import { getErrorMessage } from "@/lib/errors";
import { formatCurrency } from "@/lib/format";
import type { GeracaoDocumento, NegocioPendente } from "@/types";

const API_BASE = import.meta.env.VITE_API_URL ?? "";

// O nome do negocio na Solarz vem como "Comercial - Fulano". Pro card, so o cliente.
function nomeCliente(nomeNegocio: string | null, id: number) {
  if (!nomeNegocio) return `Negocio ${id}`;
  const partes = nomeNegocio.split(" - ");
  return (partes.length > 1 ? partes.slice(1).join(" - ") : nomeNegocio).trim();
}

export function GeracaoDocumentosPage() {
  const { showSuccess, showError } = useToast();
  const [pendentes, setPendentes] = useState<NegocioPendente[] | null>(null);
  const [geradas, setGeradas] = useState<GeracaoDocumento[]>([]);
  const [selecionado, setSelecionado] = useState<NegocioPendente | null>(null);
  const [cft, setCft] = useState("");
  const [pedido, setPedido] = useState("");
  const [gerando, setGerando] = useState(false);
  const timer = useRef<number | null>(null);

  const load = useCallback(async () => {
    try {
      const [p, g] = await Promise.all([geracaoDocumentosApi.pendentes(), geracaoDocumentosApi.list()]);
      setPendentes(p.data);
      setGeradas(g.data);
    } catch (err) {
      setPendentes([]);
      showError(getErrorMessage(err));
    }
  }, [showError]);

  useEffect(() => {
    load();
  }, [load]);

  // Enquanto algum documento estiver sendo gerado, recarrega sozinho.
  useEffect(() => {
    if (!geradas.some((g) => g.status === "processando")) return;
    timer.current = window.setTimeout(load, 4000);
    return () => {
      if (timer.current) window.clearTimeout(timer.current);
    };
  }, [geradas, load]);

  const abrirForm = async (negocio: NegocioPendente) => {
    setSelecionado(negocio);
    setCft("");
    try {
      const { numero_pedido } = await geracaoDocumentosApi.proximoPedido();
      setPedido(numero_pedido);
    } catch {
      setPedido("");
    }
  };

  const gerar = async () => {
    if (!selecionado) return;
    if (!cft.trim()) {
      showError("Informe o numero do CFT.");
      return;
    }
    if (!pedido.trim()) {
      showError("Informe o numero do pedido.");
      return;
    }
    setGerando(true);
    try {
      await geracaoDocumentosApi.gerar({
        solarz_deal_id: selecionado.solarz_deal_id,
        numero_cft: cft.trim(),
        numero_pedido: pedido.trim(),
      });
      showSuccess("Gerando os documentos.");
      setSelecionado(null);
      load();
    } catch (err) {
      showError(getErrorMessage(err));
    } finally {
      setGerando(false);
    }
  };

  if (!pendentes) return <FullPageSpinner />;

  return (
    <div className="flex flex-col gap-5 p-4 md:p-6">
      <div className="flex justify-end">
        <button
          onClick={load}
          title="Atualizar"
          aria-label="Atualizar"
          className="border border-border bg-white p-2 text-ink-secondary transition-colors hover:bg-canvas hover:text-ink"
        >
          <IconRefresh width={18} height={18} />
        </button>
      </div>

      {/* Negocios que chegaram no estagio "Gerar Documentacao" da Solarz */}
      <section className="flex flex-col gap-2">
        <div className="flex items-center gap-2 border-b border-border pb-2">
          <span className="text-sm font-medium text-ink">Para gerar</span>
          <span className="text-xs text-ink-faint">{pendentes.length}</span>
        </div>

        {pendentes.length === 0 ? (
          <p className="py-6 text-center text-xs text-ink-faint">
            Nenhum negocio aguardando geracao no momento.
          </p>
        ) : (
          <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
            {pendentes.map((n) => (
              <button
                key={n.solarz_deal_id}
                onClick={() => abrirForm(n)}
                className="w-full border border-border bg-white p-4 text-left transition hover:border-google-blue hover:shadow-sm"
              >
                <div className="text-sm font-medium text-ink">
                  {nomeCliente(n.nome_negocio, n.solarz_deal_id)}
                </div>
                <div className="mt-1 text-xs text-ink-secondary">
                  Memorial, Contrato, Procuracao e RT
                </div>
                <div className="mt-3 flex flex-wrap gap-2">
                  {n.valor_projeto ? <Badge tone="blue">{formatCurrency(n.valor_projeto)}</Badge> : null}
                  {n.ja_gerado ? <Badge tone="yellow">ja gerado antes</Badge> : null}
                </div>
              </button>
            ))}
          </div>
        )}
      </section>

      {/* Historico: o card vem pra ca depois de gerado, com os dados guardados */}
      <section className="flex flex-col gap-2">
        <div className="flex items-center gap-2 border-b border-border pb-2">
          <span className="text-sm font-medium text-ink">Gerados</span>
          <span className="text-xs text-ink-faint">{geradas.length}</span>
        </div>

        {geradas.length === 0 ? (
          <p className="py-6 text-center text-xs text-ink-faint">Nenhum documento gerado ainda.</p>
        ) : (
          <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
            {geradas.map((g) => (
              <div key={g.id} className="flex flex-col border border-border bg-white p-4">
                <div className="flex items-start justify-between gap-2">
                  <div className="min-w-0">
                    <div className="truncate text-sm font-medium text-ink">
                      {g.cliente_nome ?? `Negocio ${g.solarz_deal_id}`}
                    </div>
                    <div className="mt-1 text-xs text-ink-faint">{g.projeto_codigo}</div>
                  </div>
                  {g.status === "pronto" ? (
                    <Badge tone="green">pronto</Badge>
                  ) : g.status === "erro" ? (
                    <Badge tone="red">erro</Badge>
                  ) : (
                    <Badge tone="yellow">gerando</Badge>
                  )}
                </div>

                <div className="mt-2 text-xs text-ink-secondary">
                  Pedido {g.numero_pedido} &nbsp;|&nbsp; CFT {g.numero_cft}
                </div>
                <div className="mt-0.5 text-xs text-ink-faint">
                  {new Date(g.criado_em).toLocaleString("pt-BR")}
                </div>

                {g.status === "processando" && (
                  <div className="mt-3 flex items-center gap-2">
                    <span className="h-3 w-3 animate-spin rounded-full border-2 border-google-blue border-t-transparent" />
                    <span className="text-xs text-ink-secondary">Gerando os arquivos...</span>
                  </div>
                )}

                {g.status === "erro" && <p className="mt-3 text-xs text-google-red">{g.erro}</p>}

                {g.status === "pronto" && (
                  <a
                    href={`${API_BASE}/api/v1/geracao-documentos/${g.id}/download`}
                    className="mt-3 flex items-center justify-center gap-2 border border-border px-3 py-2 text-xs font-medium text-google-blue transition-colors hover:bg-canvas"
                  >
                    <IconFile width={16} height={16} />
                    Baixar todos ({g.arquivos.length})
                  </a>
                )}
              </div>
            ))}
          </div>
        )}
      </section>

      {selecionado && (
        <Modal
          title={`Gerar documentos - ${nomeCliente(selecionado.nome_negocio, selecionado.solarz_deal_id)}`}
          onClose={() => setSelecionado(null)}
          size="sm"
          footer={
            <>
              <Button variant="text" onClick={() => setSelecionado(null)}>
                Cancelar
              </Button>
              <Button onClick={gerar} disabled={gerando}>
                {gerando ? "Gerando..." : "Gerar documentos"}
              </Button>
            </>
          }
        >
          <div className="flex flex-col gap-4">
            <Input
              label="Numero do pedido"
              required
              value={pedido}
              onChange={(e) => setPedido(e.target.value)}
              placeholder="01"
            />
            <Input
              label="CFT"
              required
              value={cft}
              onChange={(e) => setCft(e.target.value)}
              placeholder="CFT2605857078"
            />
          </div>
        </Modal>
      )}
    </div>
  );
}
