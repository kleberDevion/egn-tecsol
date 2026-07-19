import { createCrudApi } from "./resource";
import type { Geracao, GeracaoInput } from "@/types";

export const geracaoApi = createCrudApi<Geracao, GeracaoInput>("/geracao");
