import { api, buildQuery } from "./client";
import type { ListParams } from "./resource";
import type { ActivityLogEntry, PaginatedResponse, PresencaEntry } from "@/types";

export const adminApi = {
  activity: (params: ListParams = {}) =>
    api.get<PaginatedResponse<ActivityLogEntry>>(`/admin/activity${buildQuery(params)}`),
  presenca: () => api.get<{ data: PresencaEntry[] }>("/admin/presenca"),
  getConfiguracoes: () => api.get<{ max_admin_contas: number }>("/admin/configuracoes"),
  updateConfiguracoes: (max_admin_contas: number) =>
    api.patch<{ max_admin_contas: number }>("/admin/configuracoes", { max_admin_contas }),
};
