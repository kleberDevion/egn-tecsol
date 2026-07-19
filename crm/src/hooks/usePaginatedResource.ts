import { useEffect, useState } from "react";
import type { PaginatedResponse, Pagination } from "@/types";
import type { ListParams } from "@/api/resource";
import { getErrorMessage } from "@/lib/errors";

const PER_PAGE = 10;

export function usePaginatedResource<T>(
  fetcher: (params: ListParams) => Promise<PaginatedResponse<T>>,
  filters: Record<string, string | number | undefined> = {},
) {
  const [page, setPage] = useState(1);
  const [data, setData] = useState<T[]>([]);
  const [pagination, setPagination] = useState<Pagination | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  const filtersKey = JSON.stringify(filters);

  useEffect(() => {
    setPage(1);
  }, [filtersKey]);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    fetcher({ page, per_page: PER_PAGE, ...filters })
      .then((res) => {
        if (cancelled) return;
        setData(res.data);
        setPagination(res.pagination);
      })
      .catch((err) => {
        if (cancelled) return;
        setError(getErrorMessage(err));
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page, filtersKey, reloadKey]);

  return {
    data,
    pagination,
    loading,
    error,
    page,
    setPage,
    reload: () => setReloadKey((k) => k + 1),
  };
}
