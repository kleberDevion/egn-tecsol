import { useState, type FormEvent } from "react";
import type { Geracao, GeracaoInput } from "@/types";
import { Input, Select } from "@/components/ui/Field";
import { Button } from "@/components/ui/Button";
import { Modal } from "@/components/ui/Modal";
import { NOMES_MESES } from "@/lib/format";

interface GeracaoFormProps {
  usinaId: number;
  geracao?: Geracao;
  onSubmit: (input: GeracaoInput) => Promise<void>;
  onClose: () => void;
}

export function GeracaoForm({ usinaId, geracao, onSubmit, onClose }: GeracaoFormProps) {
  const [values, setValues] = useState({
    ano: geracao?.ano ?? new Date().getFullYear(),
    mes: geracao?.mes ?? 1,
    valor_kwh: geracao?.valor_kwh ?? 0,
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!values.valor_kwh) {
      setError("Informe o valor gerado em kWh.");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await onSubmit({ usina_id: usinaId, ano: values.ano, mes: values.mes, valor_kwh: values.valor_kwh });
    } catch {
      setSaving(false);
    }
  };

  return (
    <Modal
      title={geracao ? "Editar geração" : "Nova geração mensal"}
      onClose={onClose}
      size="sm"
      footer={
        <>
          <Button variant="text" onClick={onClose} disabled={saving}>
            Cancelar
          </Button>
          <Button variant="primary" form="geracao-form" type="submit" disabled={saving}>
            {saving ? "Salvando..." : "Salvar"}
          </Button>
        </>
      }
    >
      <form id="geracao-form" onSubmit={handleSubmit} className="grid grid-cols-2 gap-4">
        <Input
          label="Ano"
          type="number"
          required
          value={values.ano}
          onChange={(e) => setValues({ ...values, ano: Number(e.target.value) })}
        />
        <Select
          label="Mês"
          required
          value={values.mes}
          onChange={(e) => setValues({ ...values, mes: Number(e.target.value) })}
        >
          {NOMES_MESES.map((nome, idx) => (
            <option key={nome} value={idx + 1}>
              {nome}
            </option>
          ))}
        </Select>
        <div className="col-span-2">
          <Input
            label="Valor gerado (kWh)"
            type="number"
            step="0.01"
            required
            value={values.valor_kwh || ""}
            onChange={(e) => setValues({ ...values, valor_kwh: Number(e.target.value) })}
          />
        </div>
        {error && <p className="col-span-2 text-sm text-google-red">{error}</p>}
      </form>
    </Modal>
  );
}
