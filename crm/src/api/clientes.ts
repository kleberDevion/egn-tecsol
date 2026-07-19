import { createCrudApi } from "./resource";
import type { Cliente, ClienteInput } from "@/types";

export const clientesApi = createCrudApi<Cliente, ClienteInput>("/clientes");
