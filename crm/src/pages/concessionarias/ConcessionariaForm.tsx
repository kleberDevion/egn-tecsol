import { useState, type FormEvent } from "react";
import type { Concessionaria, ConcessionariaInput } from "@/types";
import { Input } from "@/components/ui/Field";
import { Button } from "@/components/ui/Button";
import { Modal } from "@/components/ui/Modal";

interface ConcessionariaFormProps {
  concessionaria?: Concessionaria;
  onSubmit: (input: ConcessionariaInput) => Promise<void>;
  onClose: () => void;
}

export function ConcessionariaForm({ concessionaria, onSubmit, onClose }: ConcessionariaFormProps) {
  const [nome, setNome] = useState(concessionaria?.nome ?? "");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!nome.trim()) {
      setError("Informe o nome da concessionária.");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await onSubmit({ nome });
    } catch {
      setSaving(false);
    }
  };

  return (
    <Modal
      title={concessionaria ? "Editar concessionária" : "Nova concessionária"}
      onClose={onClose}
      size="sm"
      footer={
        <>
          <Button variant="text" onClick={onClose} disabled={saving}>
            Cancelar
          </Button>
          <Button variant="primary" form="concessionaria-form" type="submit" disabled={saving}>
            {saving ? "Salvando..." : "Salvar"}
          </Button>
        </>
      }
    >
      <form id="concessionaria-form" onSubmit={handleSubmit}>
        <Input label="Nome" required value={nome} onChange={(e) => setNome(e.target.value)} />
        {error && <p className="mt-2 text-sm text-google-red">{error}</p>}
      </form>
    </Modal>
  );
}
