import { api, buildQuery } from "./client";
import { createCrudApi, type ListParams } from "./resource";
import type { Geracao, PaginatedResponse, Usina, UsinaInput } from "@/types";

export const usinasApi = {
  ...createCrudApi<Usina, UsinaInput>("/usinas"),
  listGeracao: (usinaId: number, params: ListParams = {}) =>
    api.get<PaginatedResponse<Geracao>>(`/usinas/${usinaId}/geracao${buildQuery(params)}`),
};
