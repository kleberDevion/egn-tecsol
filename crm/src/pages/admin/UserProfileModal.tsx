import { useEffect, useState } from "react";
import type { Grupo, GrupoChave, Papel, UsuarioAdmin } from "@/types";
import { Modal } from "@/components/ui/Modal";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { CheckboxGroup, Select } from "@/components/ui/Field";
import { Avatar } from "@/components/ui/Avatar";
import { formatDateTime } from "@/lib/format";
import { gruposApi } from "@/api/grupos";

interface UserProfileModalProps {
  usuario: UsuarioAdmin;
  isSelf: boolean;
  onClose: () => void;
  onSave: (input: { papel: Papel; ativo: number; grupos: GrupoChave[] }) => Promise<void>;
}

export function UserProfileModal({ usuario, isSelf, onClose, onSave }: UserProfileModalProps) {
  const [papel, setPapel] = useState<Papel>(usuario.papel);
  const [ativo, setAtivo] = useState<number>(usuario.ativo);
  const [grupos, setGrupos] = useState<GrupoChave[]>(usuario.grupos);
  const [gruposDisponiveis, setGruposDisponiveis] = useState<Grupo[]>([]);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    gruposApi.list().then((res) => setGruposDisponiveis(res.data));
  }, []);

  const gruposIguais =
    grupos.length === usuario.grupos.length && grupos.every((g) => usuario.grupos.includes(g));
  const changed = papel !== usuario.papel || ativo !== usuario.ativo || !gruposIguais;

  const handleSave = async () => {
    setSaving(true);
    try {
      await onSave({ papel, ativo, grupos });
      onClose();
    } catch {
      setSaving(false);
    }
  };

  return (
    <Modal
      title="Perfil do usuário"
      onClose={onClose}
      size="sm"
      footer={
        <>
          <Button variant="text" onClick={onClose}>
            Fechar
          </Button>
          <Button variant="primary" onClick={handleSave} disabled={!changed || saving || isSelf}>
            {saving ? "Salvando..." : "Salvar permissões"}
          </Button>
        </>
      }
    >
      <div className="flex flex-col gap-5">
        <div className="flex items-center gap-3">
          <Avatar nome={usuario.nome} fotoUrl={usuario.foto_url} size={48} />
          <div>
            <p className="font-medium text-ink">{usuario.nome}</p>
            <p className="text-sm text-ink-secondary">{usuario.email}</p>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <p className="mb-1 text-xs text-ink-faint">Último login</p>
            <p className="text-ink">{formatDateTime(usuario.ultimo_login_em)}</p>
          </div>
          <div>
            <p className="mb-1 text-xs text-ink-faint">Criado em</p>
            <p className="text-ink">{formatDateTime(usuario.criado_em)}</p>
          </div>
        </div>

        <Select
          label="Papel"
          value={papel}
          disabled={isSelf}
          onChange={(e) => setPapel(e.target.value as Papel)}
        >
          <option value="operador">Operador</option>
          <option value="admin">Administrador</option>
        </Select>

        <CheckboxGroup
          label="Grupos a que pertence"
          hint="Define quais seções/ferramentas do CRM esta conta enxerga. Pode marcar mais de um."
          options={gruposDisponiveis.map((g) => ({ value: g.chave, label: g.nome }))}
          values={grupos}
          onChange={setGrupos}
        />

        <div>
          <p className="mb-1.5 text-xs font-medium text-ink-secondary">Status da conta</p>
          <div className="flex items-center gap-2">
            <Badge tone={ativo ? "green" : "red"}>{ativo ? "Ativo" : "Inativo"}</Badge>
            <Button variant="text" disabled={isSelf} onClick={() => setAtivo(ativo ? 0 : 1)}>
              {ativo ? "Desativar conta" : "Ativar conta"}
            </Button>
          </div>
        </div>

        {isSelf && (
          <p className="text-xs text-ink-faint">
            Você não pode alterar suas próprias permissões por aqui.
          </p>
        )}
      </div>
    </Modal>
  );
}
