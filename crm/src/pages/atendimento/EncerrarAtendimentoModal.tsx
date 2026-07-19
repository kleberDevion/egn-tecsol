import { useState, type FormEvent } from "react";
import { Modal } from "@/components/ui/Modal";
import { Select, Textarea, Input } from "@/components/ui/Field";
import { Button } from "@/components/ui/Button";
import type { ResultadoIndicacao } from "@/types";

export interface EncerrarAtendimentoInput {
  resultado: ResultadoIndicacao;
  valor_sistema?: number;
  tipo_contrato?: string;
  observacoes?: string;
}

const resultados: { value: ResultadoIndicacao; label: string }[] = [
  { value: "novo_contrato", label: "Novo contrato fechado" },
  { value: "em_andamento", label: "Em andamento (negociação continua)" },
  { value: "sem_interesse", label: "Sem interesse / não converteu" },
  { value: "cancelado", label: "Cancelado pelo cliente" },
];

interface EncerrarAtendimentoModalProps {
  clienteNome: string;
  onSubmit: (input: EncerrarAtendimentoInput) => void;
  onClose: () => void;
}

export function EncerrarAtendimentoModal({ clienteNome, onSubmit, onClose }: EncerrarAtendimentoModalProps) {
  const [resultado, setResultado] = useState<ResultadoIndicacao>("novo_contrato");
  const [valorSistema, setValorSistema] = useState("");
  const [tipoContrato, setTipoContrato] = useState("");
  const [observacoes, setObservacoes] = useState("");
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (resultado === "novo_contrato") {
      if (!tipoContrato.trim()) {
        setError("Informe o tipo de contrato fechado.");
        return;
      }
      if (!valorSistema || Number(valorSistema) <= 0) {
        setError("Informe o valor do sistema.");
        return;
      }
    }
    onSubmit({
      resultado,
      valor_sistema: resultado === "novo_contrato" ? Number(valorSistema) : undefined,
      tipo_contrato: resultado === "novo_contrato" ? tipoContrato.trim() : undefined,
      observacoes: observacoes.trim() || undefined,
    });
  };

  return (
    <Modal
      title={`Encerrar atendimento — ${clienteNome}`}
      onClose={onClose}
      footer={
        <>
          <Button variant="text" onClick={onClose}>
            Cancelar
          </Button>
          <Button variant="primary" form="encerrar-atendimento-form" type="submit">
            Confirmar encerramento
          </Button>
        </>
      }
    >
      <form id="encerrar-atendimento-form" onSubmit={handleSubmit} className="flex flex-col gap-4">
        <Select
          label="Resultado do atendimento"
          required
          value={resultado}
          onChange={(e) => setResultado(e.target.value as ResultadoIndicacao)}
        >
          {resultados.map((r) => (
            <option key={r.value} value={r.value}>
              {r.label}
            </option>
          ))}
        </Select>

        {resultado === "novo_contrato" && (
          <>
            <Select label="Tipo de contrato" required value={tipoContrato} onChange={(e) => setTipoContrato(e.target.value)}>
              <option value="">Selecione...</option>
              <option value="Instalação de usina">Instalação de usina</option>
              <option value="Manutenção">Manutenção</option>
              <option value="Monitoramento">Monitoramento</option>
              <option value="Outro">Outro</option>
            </Select>
            <Input
              label="Valor do sistema (R$)"
              type="number"
              min={0}
              step="0.01"
              required
              value={valorSistema}
              onChange={(e) => setValorSistema(e.target.value)}
            />
          </>
        )}

        <Textarea
          label="Observações"
          rows={4}
          placeholder="O que foi conversado, próximos passos, dados relevantes para o CRM..."
          value={observacoes}
          onChange={(e) => setObservacoes(e.target.value)}
        />

        {error && <p className="text-sm text-google-red">{error}</p>}

        <p className="text-xs text-ink-faint">
          Esse status é enviado de volta para quem gerou a indicação deste cliente.
        </p>
      </form>
    </Modal>
  );
}
