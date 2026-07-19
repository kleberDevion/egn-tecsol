import { api, buildQuery } from "./client";
import type { ListParams } from "./resource";
import type { Indicacao, IndicacaoUpdateInput, PaginatedResponse, ResumoIndicador } from "@/types";

export const indicacoesApi = {
  list: (params: ListParams = {}) => api.get<PaginatedResponse<Indicacao>>(`/indicacoes${buildQuery(params)}`),
  get: (id: number) => api.get<Indicacao>(`/indicacoes/${id}`),
  update: (id: number, input: IndicacaoUpdateInput) => api.patch<Indicacao>(`/indicacoes/${id}`, input),
  resumo: () => api.get<{ data: ResumoIndicador[] }>("/indicacoes/resumo"),
};
