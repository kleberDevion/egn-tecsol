import { api } from "./client";
import type { GeracaoDocumento, NegocioPendente } from "@/types";

export const geracaoDocumentosApi = {
  pendentes: () => api.get<{ data: NegocioPendente[] }>("/geracao-documentos/pendentes"),
  proximoPedido: () => api.get<{ numero_pedido: string }>("/geracao-documentos/proximo-pedido"),
  list: () => api.get<{ data: GeracaoDocumento[] }>("/geracao-documentos"),
  get: (id: number) => api.get<GeracaoDocumento>(`/geracao-documentos/${id}`),
  gerar: (input: { solarz_deal_id: number; numero_cft: string; numero_pedido: string }) =>
    api.post<GeracaoDocumento>("/geracao-documentos", input),
};
