import { useCallback, useEffect, useState } from "react";
import { adminApi } from "@/api/admin";
import { usuariosApi } from "@/api/usuarios";
import { niveisApi } from "@/api/niveis";
import { indicadoresApi } from "@/api/indicadores";
import { getSocket } from "@/lib/socket";
import { useAuth } from "@/contexts/AuthContext";
import { usePaginatedResource } from "@/hooks/usePaginatedResource";
import { Table, type Column } from "@/components/ui/Table";
import { Pagination } from "@/components/ui/Pagination";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Input, Select } from "@/components/ui/Field";
import { FullPageSpinner } from "@/components/ui/Spinner";
import { useToast } from "@/components/ui/ToastProvider";
import { getErrorMessage } from "@/lib/errors";
import { acaoLabel, entidadeLabel } from "@/lib/activity";
import { formatCurrency, formatDateTime } from "@/lib/format";
import { NovaContaForm } from "./NovaContaForm";
import { UserProfileModal } from "./UserProfileModal";
import { Avatar } from "@/components/ui/Avatar";
import { IconPlus, IconSearch } from "@/components/icons";
import { gruposApi } from "@/api/grupos";
import type {
  ActivityLogEntry,
  CreateUsuarioInput,
  Grupo,
  GrupoChave,
  Indicador,
  NivelConfig,
  Papel,
  PresencaEntry,
  UsuarioAdmin,
} from "@/types";

function PresencaPanel() {
  const [presenca, setPresenca] = useState<PresencaEntry[] | null>(null);

  const load = useCallback(() => {
    adminApi.presenca().then((res) => setPresenca(res.data));
  }, []);

  useEffect(() => {
    load();
    const socket = getSocket();
    if (!socket) return;
    socket.on("presence:update", load);
    return () => {
      socket.off("presence:update", load);
    };
  }, [load]);

  if (!presenca) return <FullPageSpinner />;

  const online = presenca.filter((p) => p.online);

  return (
    <div className="bg-white p-5">
      <h3 className="mb-4 text-sm font-medium text-ink">
        Online agora ({online.length}/{presenca.length})
      </h3>
      <ul className="flex flex-col gap-2">
        {presenca.map((p) => (
          <li key={p.id} className="flex items-center justify-between gap-3 text-sm">
            <span className="flex items-center gap-2">
              <span className={`h-2 w-2 rounded-full ${p.online ? "bg-google-green" : "bg-border-strong"}`} />
              <Avatar nome={p.nome} fotoUrl={p.foto_url} size={24} />
              {p.nome}
              {p.papel === "admin" && (
                <Badge tone="blue">Admin</Badge>
              )}
            </span>
            <span className="text-xs text-ink-faint">
              {p.online ? "Online" : `Último login: ${formatDateTime(p.ultimo_login_em)}`}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}

function ContasPanel() {
  const { user: currentUser } = useAuth();
  const { showSuccess, showError } = useToast();
  const [maxAdmin, setMaxAdmin] = useState<number | null>(null);
  const [maxAdminInput, setMaxAdminInput] = useState("");
  const [savingLimite, setSavingLimite] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [perfilTarget, setPerfilTarget] = useState<UsuarioAdmin | null>(null);
  const [grupos, setGrupos] = useState<Grupo[]>([]);
  const [filtroGrupo, setFiltroGrupo] = useState<GrupoChave | "">("");
  const usuarios = usePaginatedResource<UsuarioAdmin>(usuariosApi.list);

  useEffect(() => {
    adminApi.getConfiguracoes().then((res) => {
      setMaxAdmin(res.max_admin_contas);
      setMaxAdminInput(String(res.max_admin_contas));
    });
    gruposApi.list().then((res) => setGrupos(res.data));
  }, []);

  const totalAdmins = usuarios.data.filter((u) => u.papel === "admin").length;
  const usuariosFiltrados = filtroGrupo
    ? usuarios.data.filter((u) => u.grupos.includes(filtroGrupo))
    : usuarios.data;

  const handleSalvarLimite = async () => {
    const parsed = Number(maxAdminInput);
    if (!Number.isInteger(parsed) || parsed < 1) {
      showError("Informe um número inteiro maior ou igual a 1.");
      return;
    }
    setSavingLimite(true);
    try {
      const res = await adminApi.updateConfiguracoes(parsed);
      setMaxAdmin(res.max_admin_contas);
      showSuccess("Limite de contas admin atualizado.");
    } catch (err) {
      showError(getErrorMessage(err));
    } finally {
      setSavingLimite(false);
    }
  };

  const handleCreate = async (input: CreateUsuarioInput) => {
    try {
      await usuariosApi.create(input);
      showSuccess("Conta criada com sucesso.");
      setShowForm(false);
      usuarios.reload();
    } catch (err) {
      showError(getErrorMessage(err));
      throw err;
    }
  };

  const handleSalvarPermissoes = async (
    usuario: UsuarioAdmin,
    input: { papel: Papel; ativo: number; grupos: GrupoChave[] },
  ) => {
    try {
      await usuariosApi.update(usuario.id, input);
      showSuccess("Permissões atualizadas.");
      usuarios.reload();
    } catch (err) {
      showError(getErrorMessage(err));
      throw err;
    }
  };

  const columns: Column<UsuarioAdmin>[] = [
    {
      key: "nome",
      header: "Nome",
      render: (u) => (
        <button
          onClick={() => setPerfilTarget(u)}
          className="flex items-center gap-3 py-1 pr-3 text-left hover:bg-canvas cursor-pointer"
        >
          <Avatar nome={u.nome} fotoUrl={u.foto_url} size={32} />
          <span className="font-medium text-ink">{u.nome}</span>
        </button>
      ),
    },
    { key: "email", header: "E-mail", render: (u) => u.email },
    {
      key: "papel",
      header: "Papel",
      render: (u) => <Badge tone={u.papel === "admin" ? "blue" : "gray"}>{u.papel === "admin" ? "Admin" : "Operador"}</Badge>,
    },
    {
      key: "grupos",
      header: "Grupos",
      render: (u) =>
        u.grupos.length === 0 ? (
          <span className="text-xs text-ink-faint">—</span>
        ) : (
          <div className="flex flex-wrap gap-1">
            {u.grupos.map((chave) => (
              <Badge key={chave} tone="gray">
                {grupos.find((g) => g.chave === chave)?.nome ?? chave}
              </Badge>
            ))}
          </div>
        ),
    },
    {
      key: "ativo",
      header: "Status",
      render: (u) => <Badge tone={u.ativo ? "green" : "red"}>{u.ativo ? "Ativo" : "Inativo"}</Badge>,
    },
    { key: "ultimo_login_em", header: "Último login", render: (u) => formatDateTime(u.ultimo_login_em) },
  ];

  return (
    <div className="bg-white p-5">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="text-sm font-medium text-ink">Contas</h3>
          <p className="text-xs text-ink-secondary">
            {totalAdmins} de {maxAdmin ?? "…"} contas de administrador em uso
          </p>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-40">
            <Select
              label="Filtrar por grupo"
              value={filtroGrupo}
              onChange={(e) => setFiltroGrupo(e.target.value as GrupoChave | "")}
            >
              <option value="">Todos</option>
              {grupos.map((g) => (
                <option key={g.chave} value={g.chave}>
                  {g.nome}
                </option>
              ))}
            </Select>
          </div>
          <div className="w-24">
            <Input
              label="Limite admin"
              type="number"
              min={1}
              value={maxAdminInput}
              onChange={(e) => setMaxAdminInput(e.target.value)}
            />
          </div>
          <Button variant="secondary" onClick={handleSalvarLimite} disabled={savingLimite} className="mt-6">
            Salvar
          </Button>
          <Button
            variant="primary"
            icon={<IconPlus width={18} height={18} />}
            onClick={() => setShowForm(true)}
            className="mt-6"
          >
            Nova conta
          </Button>
        </div>
      </div>

      {usuarios.loading ? (
        <FullPageSpinner />
      ) : (
        <>
          <Table columns={columns} rows={usuariosFiltrados} rowKey={(u) => u.id} />
          {!filtroGrupo && usuarios.pagination && (
            <Pagination pagination={usuarios.pagination} onPageChange={usuarios.setPage} />
          )}
        </>
      )}

      {showForm && (
        <NovaContaForm
          onSubmit={handleCreate}
          onClose={() => setShowForm(false)}
          onLocalizarUsuario={(usuario) => {
            setShowForm(false);
            setPerfilTarget(usuario);
          }}
        />
      )}

      {perfilTarget && (
        <UserProfileModal
          usuario={perfilTarget}
          isSelf={perfilTarget.id === currentUser?.id}
          onClose={() => setPerfilTarget(null)}
          onSave={(input) => handleSalvarPermissoes(perfilTarget, input)}
        />
      )}
    </div>
  );
}

function AtividadePanel() {
  const atividade = usePaginatedResource<ActivityLogEntry>(adminApi.activity);

  const columns: Column<ActivityLogEntry>[] = [
    { key: "usuario_nome", header: "Usuário", render: (row) => row.usuario_nome ?? "—" },
    { key: "acao", header: "Ação", render: (row) => acaoLabel(row.acao) },
    { key: "entidade", header: "Área", render: (row) => entidadeLabel(row.entidade) },
    { key: "descricao", header: "Descrição", render: (row) => row.descricao ?? "—" },
    { key: "criado_em", header: "Quando", render: (row) => formatDateTime(row.criado_em) },
  ];

  return (
    <div className="bg-white p-5">
      <h3 className="mb-4 text-sm font-medium text-ink">Log de atividades</h3>
      {atividade.loading ? (
        <FullPageSpinner />
      ) : atividade.data.length === 0 ? (
        <p className="text-sm text-ink-secondary">Nenhuma atividade registrada ainda.</p>
      ) : (
        <>
          <Table columns={columns} rows={atividade.data} rowKey={(row) => row.id} />
          {atividade.pagination && (
            <Pagination pagination={atividade.pagination} onPageChange={atividade.setPage} />
          )}
        </>
      )}
    </div>
  );
}

function NiveisPanel() {
  const { showSuccess, showError } = useToast();
  const [niveis, setNiveis] = useState<NivelConfig[] | null>(null);
  const [savingNivel, setSavingNivel] = useState<string | null>(null);
  const [geralValorFixo, setGeralValorFixo] = useState("");
  const [geralPercentual, setGeralPercentual] = useState("");
  const [aplicandoGeral, setAplicandoGeral] = useState(false);

  const load = useCallback(() => {
    niveisApi.list().then((res) => setNiveis(res.data));
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const handleChange = (nivel: string, field: "label" | "valor_fixo" | "percentual", value: string) => {
    setNiveis((prev) =>
      prev?.map((n) =>
        n.nivel === nivel
          ? { ...n, [field]: field === "label" ? value : Number(value) }
          : n,
      ) ?? prev,
    );
  };

  const handleSalvar = async (nivel: NivelConfig) => {
    setSavingNivel(nivel.nivel);
    try {
      await niveisApi.update(nivel.nivel, {
        label: nivel.label,
        valor_fixo: nivel.valor_fixo,
        percentual: nivel.percentual,
      });
      showSuccess(`Nível "${nivel.label}" atualizado.`);
    } catch (err) {
      showError(getErrorMessage(err));
      load();
    } finally {
      setSavingNivel(null);
    }
  };

  const handleAplicarGeral = async () => {
    if (!niveis || !geralValorFixo || !geralPercentual) {
      showError("Informe valor fixo e percentual pra aplicar em todos os níveis.");
      return;
    }
    const valor_fixo = Number(geralValorFixo);
    const percentual = Number(geralPercentual);
    setAplicandoGeral(true);
    try {
      await Promise.all(niveis.map((n) => niveisApi.update(n.nivel, { valor_fixo, percentual })));
      showSuccess("Valor fixo e percentual aplicados a todos os níveis.");
      load();
    } catch (err) {
      showError(getErrorMessage(err));
    } finally {
      setAplicandoGeral(false);
    }
  };

  if (!niveis) return <FullPageSpinner />;

  return (
    <div className="bg-white p-5">
      <h3 className="mb-1 text-sm font-medium text-ink">Níveis de comissão</h3>
      <p className="mb-4 text-xs text-ink-secondary">
        Valor fixo e percentual aplicados sobre o valor do sistema quando uma indicação fecha
      </p>

      <div className="mb-4 flex flex-wrap items-end gap-3 bg-canvas p-3">
        <div className="w-32">
          <Input
            label="Valor fixo (R$)"
            type="number"
            min={0}
            step="0.01"
            placeholder="ex: 300"
            value={geralValorFixo}
            onChange={(e) => setGeralValorFixo(e.target.value)}
          />
        </div>
        <div className="w-32">
          <Input
            label="Percentual"
            type="number"
            min={0}
            max={1}
            step="0.01"
            placeholder="ex: 0.03"
            value={geralPercentual}
            onChange={(e) => setGeralPercentual(e.target.value)}
          />
        </div>
        <Button variant="secondary" onClick={handleAplicarGeral} disabled={aplicandoGeral}>
          Aplicar a todos os níveis
        </Button>
        <p className="w-full text-xs text-ink-faint">Sobrescreve o valor fixo e o percentual de todas as categorias abaixo — o nome de cada nível não muda.</p>
      </div>

      <div className="flex flex-col gap-2">
        {niveis.map((n) => (
          <div key={n.nivel} className="flex flex-wrap items-end gap-3 border-b border-border pb-3 last:border-0 last:pb-0">
            <div className="w-40">
              <Input label="Nome" value={n.label} onChange={(e) => handleChange(n.nivel, "label", e.target.value)} />
            </div>
            <div className="w-32">
              <Input
                label="Valor fixo (R$)"
                type="number"
                min={0}
                step="0.01"
                value={n.valor_fixo}
                onChange={(e) => handleChange(n.nivel, "valor_fixo", e.target.value)}
              />
            </div>
            <div className="w-32">
              <Input
                label="Percentual"
                type="number"
                min={0}
                max={1}
                step="0.01"
                value={n.percentual}
                onChange={(e) => handleChange(n.nivel, "percentual", e.target.value)}
              />
            </div>
            <Button variant="secondary" onClick={() => handleSalvar(n)} disabled={savingNivel === n.nivel}>
              Salvar
            </Button>
          </div>
        ))}
      </div>
    </div>
  );
}

function ParceirosPanel() {
  const [nome, setNome] = useState("");
  const parceiros = usePaginatedResource<Indicador>(indicadoresApi.list);

  const filtered = parceiros.data.filter((p) => p.nome.toLowerCase().includes(nome.trim().toLowerCase()));

  const columns: Column<Indicador>[] = [
    { key: "nome", header: "Nome", render: (p) => <span className="font-medium text-ink">{p.nome}</span> },
    { key: "email", header: "E-mail", render: (p) => p.email },
    { key: "codigo_indicacao", header: "Código", render: (p) => p.codigo_indicacao },
    { key: "nivel", header: "Nível", render: (p) => <Badge tone="blue">{p.nivel}</Badge> },
    { key: "total_vendas", header: "Vendas", render: (p) => p.total_vendas },
    { key: "total_ganhos", header: "Total ganho", render: (p) => formatCurrency(p.total_ganhos) },
  ];

  return (
    <div className="bg-white p-5">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <h3 className="text-sm font-medium text-ink">Parceiros (app de indicações)</h3>
        <div className="relative w-full max-w-xs">
          <IconSearch width={16} height={16} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-ink-faint" />
          <input
            value={nome}
            onChange={(e) => setNome(e.target.value)}
            placeholder="Buscar por nome"
            className="w-full border border-border bg-white py-2 pl-9 pr-4 text-sm outline-none focus:border-google-blue focus:ring-2 focus:ring-google-blue-bg"
          />
        </div>
      </div>

      {parceiros.loading ? (
        <FullPageSpinner />
      ) : filtered.length === 0 ? (
        <p className="text-sm text-ink-secondary">Nenhum parceiro cadastrado ainda.</p>
      ) : (
        <>
          <Table columns={columns} rows={filtered} rowKey={(p) => p.id} />
          {parceiros.pagination && <Pagination pagination={parceiros.pagination} onPageChange={parceiros.setPage} />}
        </>
      )}
    </div>
  );
}

export function AdminPage() {
  const { user } = useAuth();

  if (!user) return null;

  return (
    <div className="flex flex-col gap-px bg-border p-px">
      <PresencaPanel />
      <ContasPanel />
      <NiveisPanel />
      <ParceirosPanel />
      <AtividadePanel />
    </div>
  );
}
