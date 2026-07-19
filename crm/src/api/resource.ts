import { api, buildQuery } from "./client";
import type { PaginatedResponse } from "@/types";

export interface ListParams {
  page?: number;
  per_page?: number;
  [key: string]: string | number | undefined;
}

export function createCrudApi<T, TInput>(basePath: string) {
  return {
    list: (params: ListParams = {}) =>
      api.get<PaginatedResponse<T>>(`${basePath}${buildQuery(params)}`),
    get: (id: number) => api.get<T>(`${basePath}/${id}`),
    create: (input: TInput) => api.post<T>(basePath, input),
    replace: (id: number, input: TInput) => api.put<T>(`${basePath}/${id}`, input),
    update: (id: number, input: Partial<TInput>) => api.patch<T>(`${basePath}/${id}`, input),
    remove: (id: number) => api.delete(`${basePath}/${id}`),
  };
}
