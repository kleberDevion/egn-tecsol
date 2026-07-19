import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { usinasApi } from "@/api/usinas";
import type { Usina, UsinaInput } from "@/types";
import { usePaginatedResource } from "@/hooks/usePaginatedResource";
import { useClientesLookup } from "@/hooks/useClientesLookup";
import { PageHeader } from "@/components/ui/PageHeader";
import { Button } from "@/components/ui/Button";
import { IconButton } from "@/components/ui/IconButton";
import { Table, type Column } from "@/components/ui/Table";
import { Pagination } from "@/components/ui/Pagination";
import { EmptyState } from "@/components/ui/EmptyState";
import { FullPageSpinner } from "@/components/ui/Spinner";
import { ConfirmDialog } from "@/components/ui/ConfirmDialog";
import { UsinaForm } from "./UsinaForm";
import { IconBolt, IconPencil, IconPlus, IconSearch, IconTrash } from "@/components/icons";
import { useToast } from "@/components/ui/ToastProvider";
import { getErrorMessage } from "@/lib/errors";
import { formatCurrency, formatDate } from "@/lib/format";

export function UsinasPage() {
  const navigate = useNavigate();
  const { nomeById } = useClientesLookup();
  const [nome, setNome] = useState("");
  const [formTarget, setFormTarget] = useState<Usina | "new" | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<Usina | null>(null);
  const [deleting, setDeleting] = useState(false);
  const { showSuccess, showError } = useToast();

  const { data, pagination, loading, error, setPage, reload } = usePaginatedResource(
    usinasApi.list,
    { nome },
  );

  const handleSubmit = async (input: UsinaInput) => {
    try {
      if (formTarget && formTarget !== "new") {
        await usinasApi.replace(formTarget.id, input);
        showSuccess("Usina atualizada com sucesso.");
      } else {
        await usinasApi.create(input);
        showSuccess("Usina criada com sucesso.");
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
      await usinasApi.remove(deleteTarget.id);
      showSuccess("Usina removida.");
      setDeleteTarget(null);
      reload();
    } catch (err) {
      showError(getErrorMessage(err));
    } finally {
      setDeleting(false);
    }
  };

  const columns: Column<Usina>[] = [
    { key: "nome", header: "Nome", render: (u) => <span className="font-medium">{u.nome}</span> },
    { key: "potencia_kwp", header: "Potência", render: (u) => `${u.potencia_kwp} kWp` },
    { key: "data_instalacao", header: "Instalação", render: (u) => formatDate(u.data_instalacao) },
    { key: "total_investido", header: "Investido", render: (u) => formatCurrency(u.total_investido) },
    { key: "cliente", header: "Cliente", render: (u) => nomeById(u.cliente_id) },
    {
      key: "acoes",
      header: "",
      className: "text-right",
      render: (u) => (
        <div className="flex justify-end gap-1" onClick={(e) => e.stopPropagation()}>
          <IconButton label="Editar" onClick={() => setFormTarget(u)}>
            <IconPencil width={17} height={17} />
          </IconButton>
          <IconButton label="Excluir" tone="danger" onClick={() => setDeleteTarget(u)}>
            <IconTrash width={17} height={17} />
          </IconButton>
        </div>
      ),
    },
  ];

  return (
    <div className="p-6">
      <PageHeader
        action={
          <Button variant="primary" icon={<IconPlus width={18} height={18} />} onClick={() => setFormTarget("new")}>
            Nova usina
          </Button>
        }
      />

      <div className="relative mb-4 w-full max-w-xs">
        <IconSearch width={16} height={16} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-ink-faint" />
        <input
          value={nome}
          onChange={(e) => setNome(e.target.value)}
          placeholder="Buscar por nome"
          className="w-full border border-border bg-white py-2 pl-9 pr-4 text-sm outline-none focus:border-google-blue focus:ring-2 focus:ring-google-blue-bg"
        />
      </div>

      {loading ? (
        <FullPageSpinner />
      ) : error ? (
        <EmptyState icon={<IconBolt width={32} height={32} />} title="Não foi possível carregar as usinas" description={error} />
      ) : data.length === 0 ? (
        <EmptyState icon={<IconBolt width={32} height={32} />} title="Nenhuma usina encontrada" />
      ) : (
        <>
          <Table columns={columns} rows={data} rowKey={(u) => u.id} onRowClick={(u) => navigate(`/usinas/${u.id}`)} />
          {pagination && <Pagination pagination={pagination} onPageChange={setPage} />}
        </>
      )}

      {formTarget && (
        <UsinaForm
          usina={formTarget !== "new" ? formTarget : undefined}
          onSubmit={handleSubmit}
          onClose={() => setFormTarget(null)}
        />
      )}

      {deleteTarget && (
        <ConfirmDialog
          title="Excluir usina"
          message={`Tem certeza que deseja excluir "${deleteTarget.nome}"? Os registros de geração também serão removidos.`}
          busy={deleting}
          onConfirm={handleDelete}
          onCancel={() => setDeleteTarget(null)}
        />
      )}
    </div>
  );
}
