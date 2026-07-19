import type { Pagination as PaginationType } from "@/types";
import { IconButton } from "./IconButton";
import { IconChevronLeft, IconChevronRight } from "@/components/icons";

interface PaginationProps {
  pagination: PaginationType;
  onPageChange: (page: number) => void;
}

export function Pagination({ pagination, onPageChange }: PaginationProps) {
  const { page, total_pages, total_items, per_page } = pagination;
  const start = total_items === 0 ? 0 : (page - 1) * per_page + 1;
  const end = Math.min(page * per_page, total_items);

  return (
    <div className="flex items-center justify-between px-1 py-3 text-sm text-ink-secondary">
      <span>
        {total_items === 0 ? "Nenhum resultado" : `${start}–${end} de ${total_items}`}
      </span>
      <div className="flex items-center gap-1">
        <IconButton
          label="Página anterior"
          disabled={page <= 1}
          onClick={() => onPageChange(page - 1)}
        >
          <IconChevronLeft />
        </IconButton>
        <span className="px-2 text-xs">
          Página {page} de {total_pages}
        </span>
        <IconButton
          label="Próxima página"
          disabled={page >= total_pages}
          onClick={() => onPageChange(page + 1)}
        >
          <IconChevronRight />
        </IconButton>
      </div>
    </div>
  );
}
