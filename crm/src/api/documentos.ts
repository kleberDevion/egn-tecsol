import { api, ApiError, BASE_URL, buildQuery } from "./client";
import type { ListParams } from "./resource";
import type { ApiErrorBody, Documento, PaginatedResponse } from "@/types";

async function upload(projetoId: number, categoria: string, arquivo: File): Promise<Documento> {
  const form = new FormData();
  form.append("projeto_id", String(projetoId));
  form.append("categoria", categoria);
  form.append("arquivo", arquivo);
  // Precisa do BASE_URL: caminho relativo cairia no proprio CRM, nao na API.
  const response = await fetch(`${BASE_URL}/documentos`, {
    method: "POST",
    credentials: "include",
    body: form,
  });
  const body = await response.json().catch(() => null);
  if (!response.ok) {
    const errorBody = body as ApiErrorBody | null;
    throw new ApiError(
      errorBody?.error?.code ?? "UNKNOWN_ERROR",
      errorBody?.error?.message ?? "Erro ao enviar o documento",
      response.status,
    );
  }
  return body as Documento;
}

export const documentosApi = {
  list: (params: ListParams = {}) => api.get<PaginatedResponse<Documento>>(`/documentos${buildQuery(params)}`),
  get: (id: number) => api.get<Documento>(`/documentos/${id}`),
  upload,
  updateCategoria: (id: number, categoria: string) => api.patch<Documento>(`/documentos/${id}`, { categoria }),
  remove: (id: number) => api.delete(`/documentos/${id}`),
  downloadUrl: (id: number) => `/api/v1/documentos/${id}/arquivo`,
};
