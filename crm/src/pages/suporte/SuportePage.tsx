import { useCallback, useEffect, useRef, useState, type FormEvent } from "react";
import { suporteApi } from "@/api/suporte";
import { useAuth } from "@/contexts/AuthContext";
import { getSocket } from "@/lib/socket";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { EmptyState } from "@/components/ui/EmptyState";
import { FullPageSpinner } from "@/components/ui/Spinner";
import { useToast } from "@/components/ui/ToastProvider";
import { getErrorMessage } from "@/lib/errors";
import { formatDateTime } from "@/lib/format";
import { IconAlertCircle, IconCheckCircle, IconMessageCircle, IconSend } from "@/components/icons";
import { AvaliarModal } from "./AvaliarModal";
import type { SuporteMensagem, SuporteThread } from "@/types";

const statusBadge: Record<SuporteThread["status"], { tone: "yellow" | "gray"; label: string }> = {
  aberto: { tone: "yellow", label: "Aberto" },
  encerrado: { tone: "gray", label: "Encerrado" },
};

function MensagensList({ mensagens, selfId }: { mensagens: SuporteMensagem[]; selfId: number }) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ block: "end" });
  }, [mensagens.length]);

  if (mensagens.length === 0) {
    return <p className="text-sm text-ink-secondary">Nenhuma mensagem ainda.</p>;
  }

  return (
    <div className="space-y-3">
      {mensagens.map((m) => (
        <div key={m.id} className={`flex ${m.autor_usuario_id === selfId ? "justify-end" : "justify-start"}`}>
          <div className={`max-w-[75%] px-4 py-2 text-sm ${m.autor_usuario_id === selfId ? "bg-google-blue text-white" : "bg-canvas text-ink"}`}>
            {m.autor_usuario_id !== selfId && (
              <p className="mb-0.5 text-xs font-medium opacity-70">{m.autor_nome}</p>
            )}
            <p>{m.texto}</p>
          </div>
        </div>
      ))}
      <div ref={bottomRef} />
    </div>
  );
}

function ComposerForm({ disabled, onSend }: { disabled?: boolean; onSend: (texto: string) => Promise<void> }) {
  const [texto, setTexto] = useState("");
  const [enviando, setEnviando] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!texto.trim() || disabled) return;
    setEnviando(true);
    try {
      await onSend(texto.trim());
      setTexto("");
    } finally {
      setEnviando(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex items-center gap-2 border-t border-border p-3">
      <input
        value={texto}
        onChange={(e) => setTexto(e.target.value)}
        disabled={disabled || enviando}
        placeholder={disabled ? "Conversa encerrada" : "Digite uma mensagem..."}
        className="flex-1 border border-border bg-white px-4 py-2.5 text-sm text-ink outline-none focus:border-google-blue focus:ring-2 focus:ring-google-blue-bg disabled:bg-canvas"
      />
      <Button type="submit" variant="primary" icon={<IconSend width={16} height={16} />} disabled={disabled || enviando || !texto.trim()}>
        Enviar
      </Button>
    </form>
  );
}

function MinhaConversa({ selfId }: { selfId: number }) {
  const { showError, showSuccess } = useToast();
  const [thread, setThread] = useState<SuporteThread | null | undefined>(undefined);
  const [mensagens, setMensagens] = useState<SuporteMensagem[]>([]);
  const [avaliado, setAvaliado] = useState(true);
  const [mostrarAvaliar, setMostrarAvaliar] = useState(false);

  const carregar = useCallback(async () => {
    const t = await suporteApi.minhaThread();
    setThread(t);
    if (t) {
      const [msgs, avaliacao] = await Promise.all([
        suporteApi.mensagens(t.id),
        t.status === "encerrado" ? suporteApi.avaliacao(t.id) : Promise.resolve(null),
      ]);
      setMensagens(msgs.data);
      setAvaliado(avaliacao !== null);
    }
  }, []);

  useEffect(() => {
    carregar().catch((err) => showError(getErrorMessage(err)));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const threadIdRef = useRef<number | null>(null);
  useEffect(() => {
    threadIdRef.current = thread?.id ?? null;
  }, [thread]);

  useEffect(() => {
    const socket = getSocket();
    if (!socket) return;

    const onNova = (payload: { thread_id: number; mensagem: SuporteMensagem }) => {
      if (payload.thread_id !== threadIdRef.current) {
        setThread({
          id: payload.thread_id,
          usuario_id: selfId,
          status: "aberto",
          admin_usuario_id: null,
          criado_em: payload.mensagem.criado_em,
          encerrado_em: null,
        });
        setMensagens([payload.mensagem]);
        setAvaliado(true);
        return;
      }
      setMensagens((prev) => (prev.some((m) => m.id === payload.mensagem.id) ? prev : [...prev, payload.mensagem]));
    };

    const onEncerrado = (t: SuporteThread) => {
      if (t.id !== threadIdRef.current) return;
      setThread(t);
      setAvaliado(false);
      setMostrarAvaliar(true);
    };

    socket.on("suporte:nova", onNova);
    socket.on("suporte:encerrado", onEncerrado);
    return () => {
      socket.off("suporte:nova", onNova);
      socket.off("suporte:encerrado", onEncerrado);
    };
  }, [selfId]);

  const handleEnviar = async (texto: string) => {
    try {
      const mensagem = await suporteApi.enviar(texto, thread?.status === "aberto" ? thread.id : undefined);
      if (!thread || thread.id !== mensagem.thread_id) {
        setThread({ id: mensagem.thread_id, usuario_id: selfId, status: "aberto", admin_usuario_id: null, criado_em: mensagem.criado_em, encerrado_em: null });
        setMensagens([mensagem]);
        setAvaliado(true);
      } else {
        setMensagens((prev) => (prev.some((m) => m.id === mensagem.id) ? prev : [...prev, mensagem]));
      }
    } catch (err) {
      showError(getErrorMessage(err));
    }
  };

  const handleAvaliar = async (positiva: boolean, comentario: string) => {
    if (!thread) return;
    try {
      await suporteApi.avaliar(thread.id, positiva, comentario || undefined);
      setAvaliado(true);
      setMostrarAvaliar(false);
      showSuccess("Obrigado pela avaliação!");
    } catch (err) {
      showError(getErrorMessage(err));
    }
  };

  if (thread === undefined) return <FullPageSpinner />;

  const encerradoSemAvaliar = thread?.status === "encerrado" && !avaliado;

  return (
    <div className="flex h-[calc(100vh-4rem)] flex-col bg-white">
      <div className="flex items-center justify-between border-b border-border px-5 py-4">
        <div>
          <p className="font-medium text-ink">Suporte Tecsol</p>
          <p className="text-xs text-ink-secondary">Fale com a equipe interna da Tecsol</p>
        </div>
        {thread && <Badge tone={statusBadge[thread.status].tone}>{statusBadge[thread.status].label}</Badge>}
      </div>

      <div className="flex-1 overflow-y-auto px-5 py-4">
        {!thread ? (
          <EmptyState
            icon={<IconMessageCircle width={28} height={28} />}
            title="Nenhuma conversa ainda"
            description="Mande uma mensagem abaixo pra falar com o suporte."
          />
        ) : (
          <MensagensList mensagens={mensagens} selfId={selfId} />
        )}
      </div>

      {encerradoSemAvaliar && (
        <div className="flex items-center justify-between gap-3 border-t border-border bg-google-blue-bg/40 px-5 py-3">
          <p className="text-sm text-ink">Essa conversa foi encerrada. Como foi o atendimento?</p>
          <Button variant="primary" onClick={() => setMostrarAvaliar(true)}>
            Avaliar
          </Button>
        </div>
      )}

      <ComposerForm disabled={false} onSend={handleEnviar} />

      {mostrarAvaliar && <AvaliarModal onSubmit={handleAvaliar} onClose={() => setMostrarAvaliar(false)} />}
    </div>
  );
}

function InboxAdmin({ selfId }: { selfId: number }) {
  const { showError, showSuccess } = useToast();
  const [filtro, setFiltro] = useState<"aberto" | "encerrado" | undefined>("aberto");
  const [threads, setThreads] = useState<SuporteThread[] | null>(null);
  const [selecionadoId, setSelecionadoId] = useState<number | null>(null);
  const [mensagens, setMensagens] = useState<SuporteMensagem[]>([]);

  const carregarThreads = useCallback(() => {
    suporteApi
      .threads(filtro)
      .then((res) => setThreads(res.data))
      .catch((err) => showError(getErrorMessage(err)));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filtro]);

  useEffect(() => {
    carregarThreads();
  }, [carregarThreads]);

  useEffect(() => {
    if (selecionadoId === null) return;
    suporteApi
      .mensagens(selecionadoId)
      .then((res) => setMensagens(res.data))
      .catch((err) => showError(getErrorMessage(err)));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selecionadoId]);

  useEffect(() => {
    const socket = getSocket();
    if (!socket) return;

    const onNova = (payload: { thread_id: number; mensagem: SuporteMensagem }) => {
      carregarThreads();
      if (payload.thread_id === selecionadoId) {
        setMensagens((prev) => (prev.some((m) => m.id === payload.mensagem.id) ? prev : [...prev, payload.mensagem]));
      }
    };

    socket.on("suporte:nova", onNova);
    return () => {
      socket.off("suporte:nova", onNova);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selecionadoId]);

  const selecionado = threads?.find((t) => t.id === selecionadoId) ?? null;

  const handleEnviar = async (texto: string) => {
    if (!selecionado) return;
    try {
      const mensagem = await suporteApi.enviar(texto, selecionado.id);
      setMensagens((prev) => (prev.some((m) => m.id === mensagem.id) ? prev : [...prev, mensagem]));
      carregarThreads();
    } catch (err) {
      showError(getErrorMessage(err));
    }
  };

  const handleEncerrar = async () => {
    if (!selecionado) return;
    try {
      await suporteApi.encerrar(selecionado.id);
      showSuccess("Conversa encerrada.");
      carregarThreads();
    } catch (err) {
      showError(getErrorMessage(err));
    }
  };

  return (
    <div className="grid h-[calc(100vh-4rem)] grid-cols-1 lg:grid-cols-[320px_1fr]">
      <div className="flex flex-col border-r border-border bg-white">
        <div className="flex gap-1 border-b border-border p-2">
          {(["aberto", "encerrado", undefined] as const).map((f) => (
            <button
              key={f ?? "todos"}
              onClick={() => setFiltro(f)}
              className={`shrink-0 px-3 py-1.5 text-xs font-medium transition-colors ${
                filtro === f ? "bg-google-blue-bg text-google-blue-dark" : "text-ink-secondary hover:bg-canvas"
              }`}
            >
              {f === "aberto" ? "Abertas" : f === "encerrado" ? "Encerradas" : "Todas"}
            </button>
          ))}
        </div>

        {threads === null ? (
          <FullPageSpinner />
        ) : threads.length === 0 ? (
          <div className="p-4">
            <EmptyState icon={<IconAlertCircle width={28} height={28} />} title="Nenhuma conversa" />
          </div>
        ) : (
          <ul className="flex-1 overflow-y-auto">
            {threads.map((t) => (
              <li key={t.id}>
                <button
                  onClick={() => setSelecionadoId(t.id)}
                  className={`w-full border-b border-border px-4 py-3 text-left transition-colors hover:bg-canvas ${
                    selecionadoId === t.id ? "bg-google-blue-bg/40" : ""
                  }`}
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-medium text-ink">{t.usuario_nome}</span>
                    <Badge tone={statusBadge[t.status].tone}>{statusBadge[t.status].label}</Badge>
                  </div>
                  <p className="mt-1 truncate text-xs text-ink-secondary">{t.ultima_mensagem ?? "—"}</p>
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>

      <div className="flex flex-col bg-white">
        {!selecionado ? (
          <div className="flex flex-1 items-center justify-center">
            <EmptyState
              icon={<IconMessageCircle width={28} height={28} />}
              title="Selecione uma conversa"
              description="Escolha um operador na lista ao lado."
            />
          </div>
        ) : (
          <>
            <div className="flex items-center justify-between gap-3 border-b border-border px-5 py-4">
              <div>
                <p className="font-medium text-ink">{selecionado.usuario_nome}</p>
                <p className="text-xs text-ink-secondary">Aberta em {formatDateTime(selecionado.criado_em)}</p>
              </div>
              <div className="flex items-center gap-2">
                <Badge tone={statusBadge[selecionado.status].tone}>{statusBadge[selecionado.status].label}</Badge>
                {selecionado.status === "aberto" && (
                  <Button variant="secondary" icon={<IconCheckCircle width={16} height={16} />} onClick={handleEncerrar}>
                    Encerrar conversa
                  </Button>
                )}
              </div>
            </div>
            <div className="flex-1 overflow-y-auto px-5 py-4">
              <MensagensList mensagens={mensagens} selfId={selfId} />
            </div>
            <ComposerForm disabled={selecionado.status !== "aberto"} onSend={handleEnviar} />
          </>
        )}
      </div>
    </div>
  );
}

export function SuportePage() {
  const { user } = useAuth();
  if (!user) return null;
  return user.papel === "admin" ? <InboxAdmin selfId={user.id} /> : <MinhaConversa selfId={user.id} />;
}
