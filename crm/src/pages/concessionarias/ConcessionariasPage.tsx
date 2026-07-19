import { useState } from "react";
import { concessionariasApi } from "@/api/concessionarias";
import type { Concessionaria, ConcessionariaInput } from "@/types";
import { usePaginatedResource } from "@/hooks/usePaginatedResource";
import { Button } from "@/components/ui/Button";
import { IconButton } from "@/components/ui/IconButton";
import { Table, type Column } from "@/components/ui/Table";
import { Pagination } from "@/components/ui/Pagination";
import { EmptyState } from "@/components/ui/EmptyState";
import { FullPageSpinner } from "@/components/ui/Spinner";
import { ConfirmDialog } from "@/components/ui/ConfirmDialog";
import { ConcessionariaForm } from "./ConcessionariaForm";
import { IconBuilding, IconPencil, IconPlus, IconSearch, IconTrash } from "@/components/icons";
import { useToast } from "@/components/ui/ToastProvider";
import { getErrorMessage } from "@/lib/errors";

export function ConcessionariasPage() {
  const [nome, setNome] = useState("");
  const [formTarget, setFormTarget] = useState<Concessionaria | "new" | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<Concessionaria | null>(null);
  const [deleting, setDeleting] = useState(false);
  const { showSuccess, showError } = useToast();

  const { data, pagination, loading, error, setPage, reload } = usePaginatedResource(
    concessionariasApi.list,
  );

  const filtered = data.filter((c) => c.nome.toLowerCase().includes(nome.trim().toLowerCase()));

  const handleSubmit = async (input: ConcessionariaInput) => {
    try {
      if (formTarget && formTarget !== "new") {
        await concessionariasApi.replace(formTarget.id, input);
        showSuccess("Concessionária atualizada com sucesso.");
      } else {
        await concessionariasApi.create(input);
        showSuccess("Concessionária criada com sucesso.");
      }
      setFormTarget(null);
      reload();
    } catch (err) {
      showError(getErrorMessage(err));
      throw err;
    }
  };

  const handleDelete = async () => {
    if (!deleteTarget) return;
    setDeleting(true);
    try {
      await concessionariasApi.remove(deleteTarget.id);
      showSuccess("Concessionária removida.");
      setDeleteTarget(null);
      reload();
    } catch (err) {
      showError(getErrorMessage(err));
    } finally {
      setDeleting(false);
    }
  };

  const columns: Column<Concessionaria>[] = [
    { key: "nome", header: "Nome", render: (c) => <span className="font-medium">{c.nome}</span> },
    {
      key: "acoes",
      header: "",
      className: "text-right",
      render: (c) => (
        <div className="flex justify-end gap-1">
          <IconButton label="Editar" onClick={() => setFormTarget(c)}>
            <IconPencil width={17} height={17} />
          </IconButton>
          <IconButton label="Excluir" tone="danger" onClick={() => setDeleteTarget(c)}>
            <IconTrash width={17} height={17} />
          </IconButton>
        </div>
      ),
    },
  ];

  return (
    <div>
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border bg-white px-6 py-4">
        <div className="relative w-full max-w-xs">
          <IconSearch width={16} height={16} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-ink-faint" />
          <input
            value={nome}
            onChange={(e) => setNome(e.target.value)}
            placeholder="Buscar por nome"
            className="w-full border border-border bg-white py-2 pl-9 pr-4 text-sm outline-none focus:border-google-blue focus:ring-2 focus:ring-google-blue-bg"
          />
        </div>
        <Button variant="primary" icon={<IconPlus width={18} height={18} />} onClick={() => setFormTarget("new")}>
          Nova concessionária
        </Button>
      </div>

      <div className="p-6">
        {loading ? (
          <FullPageSpinner />
        ) : error ? (
          <EmptyState icon={<IconBuilding width={32} height={32} />} title="Não foi possível carregar as concessionárias" description={error} />
        ) : filtered.length === 0 ? (
          <EmptyState icon={<IconBuilding width={32} height={32} />} title="Nenhuma concessionária encontrada" />
        ) : (
          <>
            <Table columns={columns} rows={filtered} rowKey={(c) => c.id} />
            {pagination && <Pagination pagination={pagination} onPageChange={setPage} />}
          </>
        )}
      </div>

      {formTarget && (
        <ConcessionariaForm
          concessionaria={formTarget !== "new" ? formTarget : undefined}
          onSubmit={handleSubmit}
          onClose={() => setFormTarget(null)}
        />
      )}

      {deleteTarget && (
        <ConfirmDialog
          title="Excluir concessionária"
          message={`Tem certeza que deseja excluir "${deleteTarget.nome}"?`}
          busy={deleting}
          onConfirm={handleDelete}
          onCancel={() => setDeleteTarget(null)}
        />
      )}
    </div>
  );
}
