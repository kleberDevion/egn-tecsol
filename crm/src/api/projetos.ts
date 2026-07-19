import { api, buildQuery } from "./client";
import { createCrudApi, type ListParams } from "./resource";
import type { Documento, PaginatedResponse, Projeto, ProjetoInput } from "@/types";

export const projetosApi = {
  ...createCrudApi<Projeto, ProjetoInput>("/projetos"),
  listDocumentos: (projetoId: number, params: ListParams = {}) =>
    api.get<PaginatedResponse<Documento>>(`/projetos/${projetoId}/documentos${buildQuery(params)}`),
};
