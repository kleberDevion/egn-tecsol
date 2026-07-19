import { useEffect, useRef, useState, type FormEvent } from "react";
import type { CreateUsuarioInput, Grupo, UsuarioAdmin } from "@/types";
import { CheckboxGroup, Input, Select } from "@/components/ui/Field";
import { Button } from "@/components/ui/Button";
import { Modal } from "@/components/ui/Modal";
import { Badge } from "@/components/ui/Badge";
import { IconSearch } from "@/components/icons";
import { gruposApi } from "@/api/grupos";
import { usuariosApi } from "@/api/usuarios";

interface NovaContaFormProps {
  onSubmit: (input: CreateUsuarioInput) => Promise<void>;
  onClose: () => void;
  onLocalizarUsuario: (usuario: UsuarioAdmin) => void;
}

function LocalizarUsuarioPopover({ onSelect }: { onSelect: (usuario: UsuarioAdmin) => void }) {
  const [open, setOpen] = useState(false);
  const [busca, setBusca] = useState("");
  const [resultados, setResultados] = useState<UsuarioAdmin[]>([]);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  useEffect(() => {
    if (!open) return;
    const timer = setTimeout(() => {
      usuariosApi.list({ q: busca, per_page: 8 }).then((res) => setResultados(res.data));
    }, 250);
    return () => clearTimeout(timer);
  }, [open, busca]);

  return (
    <div className="relative" ref={ref}>
      <Button
        type="button"
        variant="secondary"
        icon={<IconSearch width={16} height={16} />}
        onClick={() => setOpen((v) => !v)}
      >
        Localizar conta existente
      </Button>

      {open && (
        <div className="absolute left-0 top-full z-20 mt-1 w-80 border border-border bg-white shadow-lg">
          <div className="border-b border-border p-2">
            <input
              autoFocus
              value={busca}
              onChange={(e) => setBusca(e.target.value)}
              placeholder="Nome ou e-mail..."
              className="w-full border border-border bg-white px-3 py-1.5 text-sm outline-none focus:border-google-blue focus:ring-2 focus:ring-google-blue-bg"
            />
          </div>
          <div className="max-h-64 overflow-y-auto">
            {resultados.length === 0 ? (
              <p className="p-3 text-sm text-ink-secondary">Nenhuma conta encontrada.</p>
            ) : (
              resultados.map((u) => (
                <div
                  key={u.id}
                  onDoubleClick={() => onSelect(u)}
                  className="flex cursor-pointer items-center justify-between gap-3 border-b border-border px-3 py-2 text-sm last:border-0 hover:bg-google-blue-bg/40"
                  title="Duplo clique pra editar"
                >
                  <div className="min-w-0">
                    <p className="truncate font-medium text-ink">{u.nome}</p>
                    <p className="truncate text-xs text-ink-secondary">{u.email}</p>
                  </div>
                  <Badge tone={u.papel === "admin" ? "blue" : "gray"}>{u.papel === "admin" ? "Admin" : "Operador"}</Badge>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export function NovaContaForm({ onSubmit, onClose, onLocalizarUsuario }: NovaContaFormProps) {
  const [values, setValues] = useState<CreateUsuarioInput>({
    nome: "",
    email: "",
    senha: "",
    papel: "operador",
    grupos: [],
  });
  const [saving, setSaving] = useState(false);
  const [grupos, setGrupos] = useState<Grupo[]>([]);

  useEffect(() => {
    gruposApi.list().then((res) => setGrupos(res.data));
  }, []);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      await onSubmit(values);
    } catch {
      setSaving(false);
    }
  };

  return (
    <Modal
      title="Nova conta"
      onClose={onClose}
      footer={
        <>
          <Button variant="text" onClick={onClose} disabled={saving}>
            Cancelar
          </Button>
          <Button variant="primary" form="nova-conta-form" type="submit" disabled={saving}>
            {saving ? "Criando..." : "Criar conta"}
          </Button>
        </>
      }
    >
      <form id="nova-conta-form" onSubmit={handleSubmit} className="flex flex-col gap-4">
        <LocalizarUsuarioPopover onSelect={onLocalizarUsuario} />
        <Input
          label="Nome"
          required
          value={values.nome}
          onChange={(e) => setValues({ ...values, nome: e.target.value })}
        />
        <Input
          label="E-mail"
          type="email"
          required
          value={values.email}
          onChange={(e) => setValues({ ...values, email: e.target.value })}
        />
        <Input
          label="Senha"
          type="password"
          required
          minLength={8}
          value={values.senha}
          onChange={(e) => setValues({ ...values, senha: e.target.value })}
        />
        <Select
          label="Papel"
          required
          value={values.papel}
          onChange={(e) => setValues({ ...values, papel: e.target.value as CreateUsuarioInput["papel"] })}
        >
          <option value="operador">Operador</option>
          <option value="admin">Administrador</option>
        </Select>
        <CheckboxGroup
          label="Grupos a que pertence"
          hint={
            values.papel === "admin"
              ? "Administradores já têm acesso a tudo — grupos são opcionais."
              : "Define quais seções/ferramentas do CRM esta conta vai enxergar. Pode marcar mais de um."
          }
          options={grupos.map((g) => ({ value: g.chave, label: g.nome }))}
          values={values.grupos}
          onChange={(grupos) => setValues({ ...values, grupos })}
        />
      </form>
    </Modal>
  );
}
