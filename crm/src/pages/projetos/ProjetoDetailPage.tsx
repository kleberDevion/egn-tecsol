import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { projetosApi } from "@/api/projetos";
import { documentosApi } from "@/api/documentos";
import type { Documento, Projeto } from "@/types";
import { usePaginatedResource } from "@/hooks/usePaginatedResource";
import { useClientesLookup } from "@/hooks/useClientesLookup";
import { Button } from "@/components/ui/Button";
import { IconButton } from "@/components/ui/IconButton";
import { Table, type Column } from "@/components/ui/Table";
import { Pagination } from "@/components/ui/Pagination";
import { EmptyState } from "@/components/ui/EmptyState";
import { FullPageSpinner } from "@/components/ui/Spinner";
import { ConfirmDialog } from "@/components/ui/ConfirmDialog";
import { DocumentoForm } from "./DocumentoForm";
import { Badge } from "@/components/ui/Badge";
import { IconArrowLeft, IconFile, IconPlus, IconTrash } from "@/components/icons";
import { useToast } from "@/components/ui/ToastProvider";
import { getErrorMessage } from "@/lib/errors";
import { formatBytes } from "@/lib/format";

export function ProjetoDetailPage() {
  const { id } = useParams<{ id: string }>();
  const projetoId = Number(id);
  const navigate = useNavigate();
  const { nomeById } = useClientesLookup();
  const { showSuccess, showError } = useToast();

  const [projeto, setProjeto] = useState<Projeto | null>(null);
  const [loadingProjeto, setLoadingProjeto] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<Documento | null>(null);
  const [deleting, setDeleting] = useState(false);

  const { data, pagination, loading, error, setPage, reload } = usePaginatedResource(
    (params) => projetosApi.listDocumentos(projetoId, params),
    {},
  );

  useEffect(() => {
    projetosApi
      .get(projetoId)
      .then(setProjeto)
      .finally(() => setLoadingProjeto(false));
  }, [projetoId]);

  const handleUpload = async (categoria: string, arquivo: File) => {
    try {
      await documentosApi.upload(projetoId, categoria, arquivo);
      showSuccess("Documento enviado com sucesso.");
      setShowForm(false);
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
      await documentosApi.remove(deleteTarget.id);
      showSuccess("Documento removido.");
      setDeleteTarget(null);
      reload();
    } catch (err) {
      showError(getErrorMessage(err));
    } finally {
      setDeleting(false);
    }
  };

  const columns: Column<Documento>[] = [
    { key: "categoria", header: "Categoria", render: (d) => <Badge tone="blue">{d.categoria}</Badge> },
    { key: "nome_arquivo", header: "Arquivo", render: (d) => <span className="font-medium">{d.nome_arquivo}</span> },
    { key: "extensao", header: "Tipo", render: (d) => (d.extensao ?? "—").toUpperCase() },
    { key: "tamanho_bytes", header: "Tamanho", render: (d) => formatBytes(d.tamanho_bytes) },
    {
      key: "acoes",
      header: "",
      className: "text-right",
      render: (d) => (
        <div className="flex justify-end gap-1" onClick={(e) => e.stopPropagation()}>
          <a
            href={documentosApi.downloadUrl(d.id)}
            target="_blank"
            rel="noreferrer"
            className="inline-flex h-8 w-8 items-center justify-center text-ink-secondary transition-colors hover:bg-canvas"
            title="Baixar"
          >
            <IconFile width={17} height={17} />
          </a>
          <IconButton label="Excluir" tone="danger" onClick={() => setDeleteTarget(d)}>
            <IconTrash width={17} height={17} />
          </IconButton>
        </div>
      ),
    },
  ];

  return (
    <div className="p-6">
      <button
        onClick={() => navigate("/projetos")}
        className="mb-4 inline-flex items-center gap-1.5 text-sm font-medium text-google-blue hover:underline"
      >
        <IconArrowLeft width={16} height={16} />
        Voltar para projetos
      </button>

      {loadingProjeto ? (
        <FullPageSpinner />
      ) : !projeto ? (
        <EmptyState icon={<IconFile width={32} height={32} />} title="Projeto não encontrado" />
      ) : (
        <>
          <div className="mb-6 flex flex-wrap items-start justify-between gap-4">
            <div>
              <h1 className="text-2xl font-medium text-ink">{projeto.codigo}</h1>
              <p className="mt-1 text-sm text-ink-secondary">
                Cliente: {nomeById(projeto.cliente_id)} · Ano: {projeto.ano}
              </p>
            </div>
            <Button variant="primary" icon={<IconPlus width={18} height={18} />} onClick={() => setShowForm(true)}>
              Novo documento
            </Button>
          </div>

          {loading ? (
            <FullPageSpinner />
          ) : error ? (
            <EmptyState icon={<IconFile width={32} height={32} />} title="Não foi possível carregar os documentos" description={error} />
          ) : data.length === 0 ? (
            <EmptyState icon={<IconFile width={32} height={32} />} title="Nenhum documento cadastrado" />
          ) : (
            <>
              <Table columns={columns} rows={data} rowKey={(d) => d.id} />
              {pagination && <Pagination pagination={pagination} onPageChange={setPage} />}
            </>
          )}
        </>
      )}

      {showForm && <DocumentoForm onSubmit={handleUpload} onClose={() => setShowForm(false)} />}

      {deleteTarget && (
        <ConfirmDialog
          title="Excluir documento"
          message={`Excluir "${deleteTarget.nome_arquivo}"? O arquivo é apagado permanentemente.`}
          busy={deleting}
          onConfirm={handleDelete}
          onCancel={() => setDeleteTarget(null)}
        />
      )}
    </div>
  );
}
