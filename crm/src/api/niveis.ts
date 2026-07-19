import { api } from "./client";
import type { NivelConfig, NivelConfigInput } from "@/types";

export const niveisApi = {
  list: () => api.get<{ data: NivelConfig[] }>("/niveis"),
  update: (nivel: string, input: NivelConfigInput) => api.patch<NivelConfig>(`/niveis/${nivel}`, input),
};
