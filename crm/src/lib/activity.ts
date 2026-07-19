export const ACAO_LABELS: Record<string, string> = {
  login: "Login",
  logout: "Logout",
  create: "Criação",
  update: "Atualização",
  delete: "Exclusão",
  change_password: "Alteração de senha",
};

export const ENTIDADE_LABELS: Record<string, string> = {
  clientes: "Cliente",
  projetos: "Projeto",
  documentos: "Documento",
  usinas: "Usina",
  geracao: "Geração",
  concessionarias: "Concessionária",
  usuarios: "Usuário",
};

export function acaoLabel(acao: string): string {
  return ACAO_LABELS[acao] ?? acao;
}

export function entidadeLabel(entidade: string | null): string {
  if (!entidade) return "—";
  return ENTIDADE_LABELS[entidade] ?? entidade;
}
