import { useState, type FormEvent } from "react";
import { Input } from "@/components/ui/Field";
import { Button } from "@/components/ui/Button";
import { Modal } from "@/components/ui/Modal";

interface DocumentoFormProps {
  onSubmit: (categoria: string, arquivo: File) => Promise<void>;
  onClose: () => void;
}

export function DocumentoForm({ onSubmit, onClose }: DocumentoFormProps) {
  const [categoria, setCategoria] = useState("");
  const [arquivo, setArquivo] = useState<File | null>(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!categoria.trim()) {
      setError("Informe a categoria do documento.");
      return;
    }
    if (!arquivo) {
      setError("Selecione um arquivo.");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await onSubmit(categoria, arquivo);
    } catch {
      setSaving(false);
    }
  };

  return (
    <Modal
      title="Novo documento"
      onClose={onClose}
      footer={
        <>
          <Button variant="text" onClick={onClose} disabled={saving}>
            Cancelar
          </Button>
          <Button variant="primary" form="documento-form" type="submit" disabled={saving}>
            {saving ? "Enviando..." : "Enviar"}
          </Button>
        </>
      }
    >
      <form id="documento-form" onSubmit={handleSubmit} className="flex flex-col gap-4">
        <Input
          label="Categoria"
          required
          placeholder="ex: Contrato, Nota Fiscal, Procuração"
          value={categoria}
          onChange={(e) => setCategoria(e.target.value)}
        />
        <label className="block">
          <span className="mb-1.5 block text-xs font-medium text-ink-secondary">
            Arquivo<span className="text-google-red"> *</span>
          </span>
          <input
            type="file"
            required
            onChange={(e) => setArquivo(e.target.files?.[0] ?? null)}
            className="w-full border border-border bg-white px-3.5 py-2.5 text-sm text-ink outline-none file:mr-3 file:border-0 file:bg-canvas file:px-3 file:py-1.5 file:text-sm focus:border-google-blue focus:ring-2 focus:ring-google-blue-bg"
          />
        </label>
        {error && <p className="text-sm text-google-red">{error}</p>}
      </form>
    </Modal>
  );
}
