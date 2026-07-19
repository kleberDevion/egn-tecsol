import { api, buildQuery } from "./client";
import type { SuporteAvaliacao, SuporteMensagem, SuporteThread } from "@/types";

export const suporteApi = {
  minhaThread: () => api.get<SuporteThread | null>("/suporte/minha-thread"),
  threads: (status?: "aberto" | "encerrado") =>
    api.get<{ data: SuporteThread[] }>(`/suporte/threads${buildQuery(status ? { status } : {})}`),
  mensagens: (threadId: number) => api.get<{ data: SuporteMensagem[] }>(`/suporte/threads/${threadId}/mensagens`),
  enviar: (texto: string, threadId?: number) =>
    api.post<SuporteMensagem>("/suporte/mensagens", threadId ? { texto, thread_id: threadId } : { texto }),
  encerrar: (threadId: number) => api.post<SuporteThread>(`/suporte/threads/${threadId}/encerrar`, {}),
  avaliacao: (threadId: number) => api.get<SuporteAvaliacao | null>(`/suporte/threads/${threadId}/avaliacao`),
  avaliar: (threadId: number, positiva: boolean, comentario?: string) =>
    api.post<SuporteAvaliacao>(`/suporte/threads/${threadId}/avaliacao`, { positiva, comentario }),
};
