import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { projetosApi } from "@/api/projetos";
import type { Projeto, ProjetoInput } from "@/types";
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
import { ProjetoForm } from "./ProjetoForm";
import { IconFolder, IconPencil, IconPlus, IconTrash } from "@/components/icons";
import { useToast } from "@/components/ui/ToastProvider";
import { getErrorMessage } from "@/lib/errors";
import { Badge } from "@/components/ui/Badge";

const STATUS_TONE = { ativo: "green", cancelado: "red", desistente: "gray" } as const;
const STATUS_LABEL = { ativo: "Ativo", cancelado: "Cancelado", desistente: "Desistente" } as const;

export function ProjetosPage() {
  const navigate = useNavigate();
  const { clientes, nomeById } = useClientesLookup();
  const [ano, setAno] = useState("");
  const [clienteId, setClienteId] = useState("");
  const [formTarget, setFormTarget] = useState<Projeto | "new" | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<Projeto | null>(null);
  const [deleting, setDeleting] = useState(false);
  const { showSuccess, showError } = useToast();

  const { data, pagination, loading, error, setPage, reload } = usePaginatedResource(
    projetosApi.list,
    { ano, cliente_id: clienteId },
  );

  const handleSubmit = async (input: ProjetoInput) => {
    try {
      if (formTarget && formTarget !== "new") {
        await projetosApi.replace(formTarget.id, input);
        showSuccess("Projeto atualizado com sucesso.");
      } else {
        await projetosApi.create(input);
        showSuccess("Projeto criado com sucesso.");
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
      await projetosApi.remove(deleteTarget.id);
      showSuccess("Projeto removido.");
      setDeleteTarget(null);
      reload();
    } catch (err) {
      showError(getErrorMessage(err));
    } finally {
      setDeleting(false);
    }
  };

  const columns: Column<Projeto>[] = [
    { key: "codigo", header: "Código", render: (p) => <span className="font-medium">{p.codigo}</span> },
    { key: "cliente", header: "Cliente", render: (p) => nomeById(p.cliente_id) },
    { key: "ano", header: "Ano", render: (p) => p.ano },
    {
      key: "status",
      header: "Status",
      render: (p) => <Badge tone={STATUS_TONE[p.status]}>{STATUS_LABEL[p.status]}</Badge>,
    },
    {
      key: "acoes",
      header: "",
      className: "text-right",
      render: (p) => (
        <div className="flex justify-end gap-1" onClick={(e) => e.stopPropagation()}>
          <IconButton label="Editar" onClick={() => setFormTarget(p)}>
            <IconPencil width={17} height={17} />
          </IconButton>
          <IconButton label="Excluir" tone="danger" onClick={() => setDeleteTarget(p)}>
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
            Novo projeto
          </Button>
        }
      />

      <div className="mb-4 flex flex-wrap gap-3">
        <select
          value={clienteId}
          onChange={(e) => setClienteId(e.target.value)}
          className="border border-border bg-white px-4 py-2 text-sm outline-none focus:border-google-blue focus:ring-2 focus:ring-google-blue-bg"
        >
          <option value="">Todos os clientes</option>
          {clientes.map((c) => (
            <option key={c.id} value={c.id}>
              {c.nome}
            </option>
          ))}
        </select>
        <input
          value={ano}
          onChange={(e) => setAno(e.target.value)}
          placeholder="Ano"
          className="w-28 border border-border bg-white px-4 py-2 text-sm outline-none focus:border-google-blue focus:ring-2 focus:ring-google-blue-bg"
        />
      </div>

      {loading ? (
        <FullPageSpinner />
      ) : error ? (
        <EmptyState icon={<IconFolder width={32} height={32} />} title="Não foi possível carregar os projetos" description={error} />
      ) : data.length === 0 ? (
        <EmptyState icon={<IconFolder width={32} height={32} />} title="Nenhum projeto encontrado" />
      ) : (
        <>
          <Table columns={columns} rows={data} rowKey={(p) => p.id} onRowClick={(p) => navigate(`/projetos/${p.id}`)} />
          {pagination && <Pagination pagination={pagination} onPageChange={setPage} />}
        </>
      )}

      {formTarget && (
        <ProjetoForm
          projeto={formTarget !== "new" ? formTarget : undefined}
          onSubmit={handleSubmit}
          onClose={() => setFormTarget(null)}
        />
      )}

      {deleteTarget && (
        <ConfirmDialog
          title="Excluir projeto"
          message={`Tem certeza que deseja excluir o projeto "${deleteTarget.codigo}"? Os documentos vinculados também serão removidos.`}
          busy={deleting}
          onConfirm={handleDelete}
          onCancel={() => setDeleteTarget(null)}
        />
      )}
    </div>
  );
}
