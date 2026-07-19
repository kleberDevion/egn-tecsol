import { api } from "./client";
import type { Grupo } from "@/types";

export const gruposApi = {
  list: () => api.get<{ data: Grupo[] }>("/grupos"),
};
