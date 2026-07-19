import { useRef, useState } from "react";
import { authApi } from "@/api/auth";
import { useAuth } from "@/contexts/AuthContext";
import { Modal } from "@/components/ui/Modal";
import { Button } from "@/components/ui/Button";
import { Avatar } from "@/components/ui/Avatar";
import { useToast } from "@/components/ui/ToastProvider";
import { getErrorMessage } from "@/lib/errors";

export function ChangePhotoModal({ onClose }: { onClose: () => void }) {
  const { user, refresh } = useAuth();
  const { showSuccess, showError } = useToast();
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  if (!user) return null;

  const handlePick = (e: React.ChangeEvent<HTMLInputElement>) => {
    const picked = e.target.files?.[0] ?? null;
    setFile(picked);
    setPreview(picked ? URL.createObjectURL(picked) : null);
  };

  const handleSave = async () => {
    if (!file) return;
    setSaving(true);
    try {
      await authApi.uploadFoto(file);
      await refresh();
      showSuccess("Foto de perfil atualizada.");
      onClose();
    } catch (err) {
      showError(getErrorMessage(err));
      setSaving(false);
    }
  };

  return (
    <Modal
      title="Alterar foto"
      onClose={onClose}
      size="sm"
      footer={
        <>
          <Button variant="text" onClick={onClose} disabled={saving}>
            Cancelar
          </Button>
          <Button variant="primary" onClick={handleSave} disabled={!file || saving}>
            {saving ? "Enviando..." : "Salvar"}
          </Button>
        </>
      }
    >
      <div className="flex flex-col items-center gap-4">
        {preview ? (
          <img src={preview} alt="Pré-visualização" className="h-24 w-24 rounded-full object-cover" />
        ) : (
          <Avatar nome={user.nome} fotoUrl={user.foto_url} size={96} />
        )}
        <input
          ref={inputRef}
          type="file"
          accept="image/png,image/jpeg,image/webp"
          onChange={handlePick}
          className="hidden"
        />
        <Button variant="secondary" type="button" onClick={() => inputRef.current?.click()}>
          Escolher imagem
        </Button>
        <p className="text-center text-xs text-ink-faint">PNG, JPG ou WEBP, até 3MB.</p>
      </div>
    </Modal>
  );
}
