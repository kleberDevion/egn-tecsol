import { useEffect, useState } from "react";
import { clientesApi } from "@/api/clientes";
import type { Cliente } from "@/types";

export function useClientesLookup() {
  const [clientes, setClientes] = useState<Cliente[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    clientesApi
      .list({ per_page: 100 })
      .then((res) => {
        if (!cancelled) setClientes(res.data);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const nomeById = (id: number | null): string => {
    if (id === null) return "—";
    return clientes.find((c) => c.id === id)?.nome ?? `#${id}`;
  };

  return { clientes, loading, nomeById };
}
