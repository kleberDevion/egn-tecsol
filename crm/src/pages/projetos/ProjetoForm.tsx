import { useState, type FormEvent } from "react";
import type { Projeto, ProjetoInput, StatusProjeto } from "@/types";
import { Input, Select } from "@/components/ui/Field";
import { Button } from "@/components/ui/Button";
import { Modal } from "@/components/ui/Modal";
import { useClientesLookup } from "@/hooks/useClientesLookup";

interface ProjetoFormProps {
  projeto?: Projeto;
  onSubmit: (input: ProjetoInput) => Promise<void>;
  onClose: () => void;
}

export function ProjetoForm({ projeto, onSubmit, onClose }: ProjetoFormProps) {
  const { clientes, loading: loadingClientes } = useClientesLookup();
  const [values, setValues] = useState({
    codigo: projeto?.codigo ?? "",
    cliente_id: projeto?.cliente_id ?? 0,
    ano: projeto?.ano ?? new Date().getFullYear(),
    pasta: projeto?.pasta ?? "",
    status: projeto?.status ?? "ativo",
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!values.codigo.trim()) {
      setError("Informe o código do projeto.");
      return;
    }
    if (!values.cliente_id) {
      setError("Selecione um cliente.");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await onSubmit({
        codigo: values.codigo,
        cliente_id: values.cliente_id,
        ano: values.ano,
        pasta: values.pasta || null,
        status: values.status,
      });
    } catch {
      setSaving(false);
    }
  };

  return (
    <Modal
      title={projeto ? "Editar projeto" : "Novo projeto"}
      onClose={onClose}
      footer={
        <>
          <Button variant="text" onClick={onClose} disabled={saving}>
            Cancelar
          </Button>
          <Button variant="primary" form="projeto-form" type="submit" disabled={saving}>
            {saving ? "Salvando..." : "Salvar"}
          </Button>
        </>
      }
    >
      <form id="projeto-form" onSubmit={handleSubmit} className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <Input
          label="Código"
          required
          placeholder="PJ-2026-1050-750-001-A"
          value={values.codigo}
          onChange={(e) => setValues({ ...values, codigo: e.target.value })}
        />
        <Input
          label="Ano"
          type="number"
          required
          value={values.ano}
          onChange={(e) => setValues({ ...values, ano: Number(e.target.value) })}
        />
        <div className="sm:col-span-2">
          <Select
            label="Cliente"
            required
            disabled={loadingClientes}
            value={values.cliente_id || ""}
            onChange={(e) => setValues({ ...values, cliente_id: Number(e.target.value) })}
          >
            <option value="">Selecione um cliente</option>
            {clientes.map((c) => (
              <option key={c.id} value={c.id}>
                {c.nome}
              </option>
            ))}
          </Select>
        </div>
        <div className="sm:col-span-2">
          <Input
            label="Pasta de origem"
            value={values.pasta}
            onChange={(e) => setValues({ ...values, pasta: e.target.value })}
          />
        </div>
        <div className="sm:col-span-2">
          <Select
            label="Status"
            required
            value={values.status}
            onChange={(e) => setValues({ ...values, status: e.target.value as StatusProjeto })}
          >
            <option value="ativo">Ativo</option>
            <option value="cancelado">Cancelado</option>
            <option value="desistente">Desistente</option>
          </Select>
        </div>
        {error && <p className="sm:col-span-2 text-sm text-google-red">{error}</p>}
      </form>
    </Modal>
  );
}
