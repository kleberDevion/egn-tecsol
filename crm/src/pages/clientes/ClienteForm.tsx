import { useState, type FormEvent } from "react";
import type { Cliente, ClienteInput } from "@/types";
import { Input, Select } from "@/components/ui/Field";
import { Button } from "@/components/ui/Button";
import { Modal } from "@/components/ui/Modal";

interface ClienteFormProps {
  cliente?: Cliente;
  onSubmit: (input: ClienteInput) => Promise<void>;
  onClose: () => void;
}

export function ClienteForm({ cliente, onSubmit, onClose }: ClienteFormProps) {
  const [values, setValues] = useState<ClienteInput>({
    tipo: cliente?.tipo ?? "PF",
    nome: cliente?.nome ?? "",
    email: cliente?.email ?? "",
    telefone: cliente?.telefone ?? "",
    cpf_cnpj: cliente?.cpf_cnpj ?? "",
    endereco: cliente?.endereco ?? "",
    cep: cliente?.cep ?? "",
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!values.nome.trim()) {
      setError("Informe o nome do cliente.");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await onSubmit({
        ...values,
        email: values.email || null,
        telefone: values.telefone || null,
        cpf_cnpj: values.cpf_cnpj || null,
        endereco: values.endereco || null,
        cep: values.cep || null,
      });
    } catch {
      setSaving(false);
    }
  };

  return (
    <Modal
      title={cliente ? "Editar cliente" : "Novo cliente"}
      onClose={onClose}
      footer={
        <>
          <Button variant="text" onClick={onClose} disabled={saving}>
            Cancelar
          </Button>
          <Button variant="primary" form="cliente-form" type="submit" disabled={saving}>
            {saving ? "Salvando..." : "Salvar"}
          </Button>
        </>
      }
    >
      <form id="cliente-form" onSubmit={handleSubmit} className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <Select
          label="Tipo"
          required
          value={values.tipo}
          onChange={(e) => setValues({ ...values, tipo: e.target.value as ClienteInput["tipo"] })}
        >
          <option value="PF">Pessoa física</option>
          <option value="PJ">Pessoa jurídica</option>
        </Select>
        <Input
          label="Nome"
          required
          value={values.nome}
          onChange={(e) => setValues({ ...values, nome: e.target.value })}
        />
        <Input
          label="E-mail"
          type="email"
          value={values.email ?? ""}
          onChange={(e) => setValues({ ...values, email: e.target.value })}
        />
        <Input
          label="Telefone"
          value={values.telefone ?? ""}
          onChange={(e) => setValues({ ...values, telefone: e.target.value })}
        />
        <Input
          label="CPF/CNPJ"
          value={values.cpf_cnpj ?? ""}
          onChange={(e) => setValues({ ...values, cpf_cnpj: e.target.value })}
        />
        <Input
          label="CEP"
          value={values.cep ?? ""}
          onChange={(e) => setValues({ ...values, cep: e.target.value })}
        />
        <div className="sm:col-span-2">
          <Input
            label="Endereço"
            value={values.endereco ?? ""}
            onChange={(e) => setValues({ ...values, endereco: e.target.value })}
          />
        </div>
        {error && <p className="sm:col-span-2 text-sm text-google-red">{error}</p>}
      </form>
    </Modal>
  );
}
