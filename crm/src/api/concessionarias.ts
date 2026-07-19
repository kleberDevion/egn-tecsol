import { createCrudApi } from "./resource";
import type { Concessionaria, ConcessionariaInput } from "@/types";

export const concessionariasApi = createCrudApi<Concessionaria, ConcessionariaInput>("/concessionarias");
