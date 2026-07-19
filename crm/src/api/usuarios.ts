import { api, buildQuery } from "./client";
import type { ListParams } from "./resource";
import type { CreateUsuarioInput, GrupoChave, PaginatedResponse, Papel, UsuarioAdmin } from "@/types";

export const usuariosApi = {
  list: (params: ListParams = {}) =>
    api.get<PaginatedResponse<UsuarioAdmin>>(`/usuarios${buildQuery(params)}`),
  create: (input: CreateUsuarioInput) => api.post<UsuarioAdmin>("/usuarios", input),
  update: (id: number, input: Partial<{ nome: string; papel: Papel; ativo: number; grupos: GrupoChave[] }>) =>
    api.patch<UsuarioAdmin>(`/usuarios/${id}`, input),
};
