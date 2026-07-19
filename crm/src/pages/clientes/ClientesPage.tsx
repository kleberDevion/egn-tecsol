import { useState } from "react";
import { clientesApi } from "@/api/clientes";
import type { Cliente, ClienteInput } from "@/types";
import { usePaginatedResource } from "@/hooks/usePaginatedResource";
import { PageHeader } from "@/components/ui/PageHeader";
import { Button } from "@/components/ui/Button";
import { IconButton } from "@/components/ui/IconButton";
import { Table, type Column } from "@/components/ui/Table";
import { Pagination } from "@/components/ui/Pagination";
import { Badge } from "@/components/ui/Badge";
import { EmptyState } from "@/components/ui/EmptyState";
import { FullPageSpinner } from "@/components/ui/Spinner";
import { ConfirmDialog } from "@/components/ui/ConfirmDialog";
import { ClienteForm } from "./ClienteForm";
import { IconPencil, IconPlus, IconSearch, IconTrash, IconUsers } from "@/components/icons";
import { useToast } from "@/components/ui/ToastProvider";
import { getErrorMessage } from "@/lib/errors";

export function ClientesPage() {
  const [nome, setNome] = useState("");
  const [tipo, setTipo] = useState("");
  const [formTarget, setFormTarget] = useState<Cliente | "new" | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<Cliente | null>(null);
  const [deleting, setDeleting] = useState(false);
  const { showSuccess, showError } = useToast();

  const { data, pagination, loading, error, setPage, reload } = usePaginatedResource(
    clientesApi.list,
    { nome, tipo },
  );

  const handleSubmit = async (input: ClienteInput) => {
    try {
      if (formTarget && formTarget !== "new") {
        await clientesApi.replace(formTarget.id, input);
        showSuccess("Cliente atualizado com sucesso.");
      } else {
        await clientesApi.create(input);
        showSuccess("Cliente criado com sucesso.");
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
      await clientesApi.remove(deleteTarget.id);
      showSuccess("Cliente removido.");
      setDeleteTarget(null);
      reload();
    } catch (err) {
      showError(getErrorMessage(err));
    } finally {
      setDeleting(false);
    }
  };

  const columns: Column<Cliente>[] = [
    { key: "nome", header: "Nome", render: (c) => <span className="font-medium">{c.nome}</span> },
    {
      key: "tipo",
      header: "Tipo",
      render: (c) => <Badge tone={c.tipo === "PJ" ? "blue" : "gray"}>{c.tipo}</Badge>,
    },
    { key: "email", header: "E-mail", render: (c) => c.email ?? "—" },
    { key: "telefone", header: "Telefone", render: (c) => c.telefone ?? "—" },
    { key: "cpf_cnpj", header: "CPF/CNPJ", render: (c) => c.cpf_cnpj ?? "—" },
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
    <div className="p-6">
      <PageHeader
        action={
          <Button variant="primary" icon={<IconPlus width={18} height={18} />} onClick={() => setFormTarget("new")}>
            Novo cliente
          </Button>
        }
      />

      <div className="mb-4 flex flex-wrap gap-3">
        <div className="relative w-full max-w-xs">
          <IconSearch width={16} height={16} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-ink-faint" />
          <input
            value={nome}
            onChange={(e) => setNome(e.target.value)}
            placeholder="Buscar por nome"
            className="w-full border border-border bg-white py-2 pl-9 pr-4 text-sm outline-none focus:border-google-blue focus:ring-2 focus:ring-google-blue-bg"
          />
        </div>
        <select
          value={tipo}
          onChange={(e) => setTipo(e.target.value)}
          className="border border-border bg-white px-4 py-2 text-sm outline-none focus:border-google-blue focus:ring-2 focus:ring-google-blue-bg"
        >
          <option value="">Todos os tipos</option>
          <option value="PF">Pessoa física</option>
          <option value="PJ">Pessoa jurídica</option>
        </select>
      </div>

      {loading ? (
        <FullPageSpinner />
      ) : error ? (
        <EmptyState icon={<IconUsers width={32} height={32} />} title="Não foi possível carregar os clientes" description={error} />
      ) : data.length === 0 ? (
        <EmptyState icon={<IconUsers width={32} height={32} />} title="Nenhum cliente encontrado" />
      ) : (
        <>
          <Table columns={columns} rows={data} rowKey={(c) => c.id} />
          {pagination && <Pagination pagination={pagination} onPageChange={setPage} />}
        </>
      )}

      {formTarget && (
        <ClienteForm
          cliente={formTarget !== "new" ? formTarget : undefined}
          onSubmit={handleSubmit}
          onClose={() => setFormTarget(null)}
        />
      )}

      {deleteTarget && (
        <ConfirmDialog
          title="Excluir cliente"
          message={`Tem certeza que deseja excluir "${deleteTarget.nome}"? Essa ação não pode ser desfeita.`}
          busy={deleting}
          onConfirm={handleDelete}
          onCancel={() => setDeleteTarget(null)}
        />
      )}
    </div>
  );
}
