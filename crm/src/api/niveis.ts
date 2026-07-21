import { api } from "./client";
import type { ComissaoNivel, NivelConfig, NivelConfigInput } from "@/types";

export const niveisApi = {
  list: () => api.get<{ data: NivelConfig[] }>("/niveis"),
  update: (nivel: string, input: NivelConfigInput) => api.patch<NivelConfig>(`/niveis/${nivel}`, input),

  listComissao: () => api.get<{ data: ComissaoNivel[] }>("/niveis/comissao"),
  updateComissao: (nivel: number, valor_por_kwh: number) =>
    api.patch<ComissaoNivel>(`/niveis/comissao/${nivel}`, { valor_por_kwh }),
};
