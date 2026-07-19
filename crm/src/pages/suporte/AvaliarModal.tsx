import { useState, type FormEvent } from "react";
import { Modal } from "@/components/ui/Modal";
import { Textarea } from "@/components/ui/Field";
import { Button } from "@/components/ui/Button";
import { IconCheckCircle, IconX } from "@/components/icons";

interface AvaliarModalProps {
  onSubmit: (positiva: boolean, comentario: string) => void;
  onClose: () => void;
}

export function AvaliarModal({ onSubmit, onClose }: AvaliarModalProps) {
  const [positiva, setPositiva] = useState<boolean | null>(null);
  const [comentario, setComentario] = useState("");
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (positiva === null) {
      setError("Escolha uma avaliação.");
      return;
    }
    onSubmit(positiva, comentario.trim());
  };

  return (
    <Modal
      title="Como foi seu atendimento?"
      onClose={onClose}
      footer={
        <>
          <Button variant="text" onClick={onClose}>
            Agora não
          </Button>
          <Button variant="primary" form="avaliar-suporte-form" type="submit">
            Enviar avaliação
          </Button>
        </>
      }
    >
      <form id="avaliar-suporte-form" onSubmit={handleSubmit} className="flex flex-col gap-4">
        <div className="flex gap-3">
          <button
            type="button"
            onClick={() => setPositiva(true)}
            className={`flex flex-1 flex-col items-center gap-2 border p-4 transition-colors ${
              positiva === true ? "border-google-green bg-google-green-bg" : "border-border hover:bg-canvas"
            }`}
          >
            <IconCheckCircle width={24} height={24} className={positiva === true ? "text-google-green" : "text-ink-faint"} />
            <span className="text-sm font-medium text-ink">Bom atendimento</span>
          </button>
          <button
            type="button"
            onClick={() => setPositiva(false)}
            className={`flex flex-1 flex-col items-center gap-2 border p-4 transition-colors ${
              positiva === false ? "border-google-red bg-google-red-bg" : "border-border hover:bg-canvas"
            }`}
          >
            <IconX width={24} height={24} className={positiva === false ? "text-google-red" : "text-ink-faint"} />
            <span className="text-sm font-medium text-ink">Poderia melhorar</span>
          </button>
        </div>

        <Textarea
          label="Comentário (opcional)"
          rows={3}
          placeholder="Conte um pouco mais, se quiser..."
          value={comentario}
          onChange={(e) => setComentario(e.target.value)}
        />

        {error && <p className="text-sm text-google-red">{error}</p>}

        <p className="text-xs text-ink-faint">Sua avaliação é anônima — só entra na estatística geral do suporte.</p>
      </form>
    </Modal>
  );
}
