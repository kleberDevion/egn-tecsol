import { useState, type FormEvent } from "react";
import type { Usina, UsinaInput } from "@/types";
import { Input, Select } from "@/components/ui/Field";
import { Button } from "@/components/ui/Button";
import { Modal } from "@/components/ui/Modal";
import { useClientesLookup } from "@/hooks/useClientesLookup";

interface UsinaFormProps {
  usina?: Usina;
  onSubmit: (input: UsinaInput) => Promise<void>;
  onClose: () => void;
}

export function UsinaForm({ usina, onSubmit, onClose }: UsinaFormProps) {
  const { clientes, loading: loadingClientes } = useClientesLookup();
  const [values, setValues] = useState({
    nome: usina?.nome ?? "",
    cliente_id: usina?.cliente_id ?? 0,
    potencia_kwp: usina?.potencia_kwp ?? 0,
    data_instalacao: usina?.data_instalacao ?? "",
    total_investido: usina?.total_investido ?? undefined,
    geracao_anual_esperada: usina?.geracao_anual_esperada ?? undefined,
    cep: usina?.cep ?? "",
    latitude: usina?.latitude ?? undefined,
    longitude: usina?.longitude ?? undefined,
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!values.nome.trim()) {
      setError("Informe o nome da usina.");
      return;
    }
    if (!values.potencia_kwp) {
      setError("Informe a potência em kWp.");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await onSubmit({
        nome: values.nome,
        cliente_id: values.cliente_id || null,
        potencia_kwp: values.potencia_kwp,
        data_instalacao: values.data_instalacao || null,
        total_investido: values.total_investido ?? null,
        geracao_anual_esperada: values.geracao_anual_esperada ?? null,
        cep: values.cep || null,
        latitude: values.latitude ?? null,
        longitude: values.longitude ?? null,
      });
    } catch {
      setSaving(false);
    }
  };

  return (
    <Modal
      title={usina ? "Editar usina" : "Nova usina"}
      onClose={onClose}
      size="lg"
      footer={
        <>
          <Button variant="text" onClick={onClose} disabled={saving}>
            Cancelar
          </Button>
          <Button variant="primary" form="usina-form" type="submit" disabled={saving}>
            {saving ? "Salvando..." : "Salvar"}
          </Button>
        </>
      }
    >
      <form id="usina-form" onSubmit={handleSubmit} className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <Input
          label="Nome"
          required
          value={values.nome}
          onChange={(e) => setValues({ ...values, nome: e.target.value })}
        />
        <Select
          label="Cliente"
          disabled={loadingClientes}
          value={values.cliente_id || ""}
          onChange={(e) => setValues({ ...values, cliente_id: Number(e.target.value) })}
        >
          <option value="">Não identificado</option>
          {clientes.map((c) => (
            <option key={c.id} value={c.id}>
              {c.nome}
            </option>
          ))}
        </Select>
        <Input
          label="Potência (kWp)"
          type="number"
          step="0.01"
          required
          value={values.potencia_kwp || ""}
          onChange={(e) => setValues({ ...values, potencia_kwp: Number(e.target.value) })}
        />
        <Input
          label="Data de instalação"
          type="date"
          value={values.data_instalacao ?? ""}
          onChange={(e) => setValues({ ...values, data_instalacao: e.target.value })}
        />
        <Input
          label="Total investido (R$)"
          type="number"
          step="0.01"
          value={values.total_investido ?? ""}
          onChange={(e) => setValues({ ...values, total_investido: e.target.value ? Number(e.target.value) : undefined })}
        />
        <Input
          label="Geração anual esperada (kWh)"
          type="number"
          step="0.01"
          value={values.geracao_anual_esperada ?? ""}
          onChange={(e) => setValues({ ...values, geracao_anual_esperada: e.target.value ? Number(e.target.value) : undefined })}
        />
        <Input
          label="CEP"
          value={values.cep ?? ""}
          onChange={(e) => setValues({ ...values, cep: e.target.value })}
        />
        <div />
        <Input
          label="Latitude"
          type="number"
          step="0.000001"
          value={values.latitude ?? ""}
          onChange={(e) => setValues({ ...values, latitude: e.target.value ? Number(e.target.value) : undefined })}
        />
        <Input
          label="Longitude"
          type="number"
          step="0.000001"
          value={values.longitude ?? ""}
          onChange={(e) => setValues({ ...values, longitude: e.target.value ? Number(e.target.value) : undefined })}
        />
        {error && <p className="sm:col-span-2 text-sm text-google-red">{error}</p>}
      </form>
    </Modal>
  );
}
