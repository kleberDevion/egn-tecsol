import { useState, type FormEvent } from "react";
import { authApi } from "@/api/auth";
import { Modal } from "@/components/ui/Modal";
import { Input } from "@/components/ui/Field";
import { Button } from "@/components/ui/Button";
import { useToast } from "@/components/ui/ToastProvider";
import { getErrorMessage } from "@/lib/errors";

export function ChangePasswordModal({ onClose }: { onClose: () => void }) {
  const { showSuccess, showError } = useToast();
  const [senhaAtual, setSenhaAtual] = useState("");
  const [senhaNova, setSenhaNova] = useState("");
  const [saving, setSaving] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setSaving(true);
    try {
      await authApi.changePassword({ senha_atual: senhaAtual, senha_nova: senhaNova });
      showSuccess("Senha alterada com sucesso");
      onClose();
    } catch (err) {
      showError(getErrorMessage(err));
      setSaving(false);
    }
  }

  return (
    <Modal
      title="Alterar senha"
      onClose={onClose}
      size="sm"
      footer={
        <>
          <Button variant="text" onClick={onClose} disabled={saving}>
            Cancelar
          </Button>
          <Button variant="primary" form="change-password-form" type="submit" disabled={saving}>
            {saving ? "Salvando..." : "Salvar"}
          </Button>
        </>
      }
    >
      <form id="change-password-form" onSubmit={handleSubmit} className="flex flex-col gap-4">
        <Input
          label="Senha atual"
          type="password"
          required
          autoComplete="current-password"
          value={senhaAtual}
          onChange={(e) => setSenhaAtual(e.target.value)}
        />
        <Input
          label="Nova senha"
          type="password"
          required
          minLength={8}
          autoComplete="new-password"
          value={senhaNova}
          onChange={(e) => setSenhaNova(e.target.value)}
        />
      </form>
    </Modal>
  );
}
