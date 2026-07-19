import { api, buildQuery } from "./client";
import type { ListParams } from "./resource";
import type { ActivityLogEntry, AvaliacoesSuporteResumo, MinhasMetricas, PaginatedResponse } from "@/types";

export const dashboardApi = {
  minhasMetricas: () => api.get<MinhasMetricas>("/dashboard/minhas-metricas"),
  minhaAtividade: (params: ListParams = {}) =>
    api.get<PaginatedResponse<ActivityLogEntry>>(`/dashboard/minha-atividade${buildQuery(params)}`),
  avaliacoesSuporte: () => api.get<AvaliacoesSuporteResumo>("/dashboard/avaliacoes-suporte"),
};
