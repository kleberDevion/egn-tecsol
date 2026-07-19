import { Modal } from "./Modal";
import { Button } from "./Button";

interface ConfirmDialogProps {
  title: string;
  message: string;
  confirmLabel?: string;
  busy?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}

export function ConfirmDialog({
  title,
  message,
  confirmLabel = "Excluir",
  busy,
  onConfirm,
  onCancel,
}: ConfirmDialogProps) {
  return (
    <Modal
      title={title}
      onClose={onCancel}
      size="sm"
      footer={
        <>
          <Button variant="text" onClick={onCancel}>
            Cancelar
          </Button>
          <Button variant="danger" onClick={onConfirm} disabled={busy}>
            {busy ? "Excluindo..." : confirmLabel}
          </Button>
        </>
      }
    >
      <p className="text-sm text-ink-secondary">{message}</p>
    </Modal>
  );
}
