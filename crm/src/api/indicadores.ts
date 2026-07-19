import { api, buildQuery } from "./client";
import type { ListParams } from "./resource";
import type { Indicador, PaginatedResponse } from "@/types";

export const indicadoresApi = {
  list: (params: ListParams = {}) => api.get<PaginatedResponse<Indicador>>(`/indicadores${buildQuery(params)}`),
};
