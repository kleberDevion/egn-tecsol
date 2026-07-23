export type Tipo = "PF" | "PJ";

export interface Cliente {
  id: number;
  tipo: Tipo;
  nome: string;
  email: string | null;
  telefone: string | null;
  cpf_cnpj: string | null;
  endereco: string | null;
  cep: string | null;
  criado_em: string;
  atualizado_em: string;
}

export type ClienteInput = Omit<Cliente, "id" | "criado_em" | "atualizado_em">;

export type StatusProjeto = "ativo" | "cancelado" | "desistente";

export interface Projeto {
  id: number;
  codigo: string;
  cliente_id: number;
  ano: number;
  pasta: string | null;
  status: StatusProjeto;
  criado_em: string;
  atualizado_em: string;
}

export type ProjetoInput = Omit<Projeto, "id" | "criado_em" | "atualizado_em">;

export interface Documento {
  id: number;
  projeto_id: number;
  categoria: string;
  nome_arquivo: string;
  extensao: string | null;
  tamanho_bytes: number | null;
  caminho_relativo: string;
  criado_em: string;
  atualizado_em: string;
}

export interface Usina {
  id: number;
  nome: string;
  cliente_id: number | null;
  potencia_kwp: number;
  data_instalacao: string | null;
  total_investido: number | null;
  geracao_anual_esperada: number | null;
  cep: string | null;
  latitude: number | null;
  longitude: number | null;
  criado_em: string;
  atualizado_em: string;
}

export type UsinaInput = Omit<Usina, "id" | "criado_em" | "atualizado_em">;

export interface Geracao {
  id: number;
  usina_id: number;
  ano: number;
  mes: number;
  valor_kwh: number;
  criado_em: string;
  atualizado_em: string;
}

export type GeracaoInput = Omit<Geracao, "id" | "criado_em" | "atualizado_em">;

export interface Concessionaria {
  id: number;
  nome: string;
  criado_em: string;
  atualizado_em: string;
}

export type ConcessionariaInput = Omit<Concessionaria, "id" | "criado_em" | "atualizado_em">;

export interface Pagination {
  page: number;
  per_page: number;
  total_items: number;
  total_pages: number;
}

export interface PaginatedResponse<T> {
  data: T[];
  pagination: Pagination;
}

export interface ApiErrorBody {
  error: {
    code: string;
    message: string;
  };
}

export type Papel = "admin" | "operador";

export type GrupoChave = "vendas" | "engenharia" | "financeiro" | "diretoria" | "marketing" | "tecnologia";

export interface Grupo {
  chave: GrupoChave;
  nome: string;
  ordem: number;
}

export interface Usuario {
  id: number;
  nome: string;
  email: string;
  papel: Papel;
  grupos: GrupoChave[];
  criado_em: string;
  ultimo_login_em: string | null;
  foto_url: string | null;
}

export interface UsuarioAdmin extends Usuario {
  ativo: number;
  atualizado_em: string;
}

export interface PresencaEntry {
  id: number;
  nome: string;
  email: string;
  papel: Papel;
  ativo: number;
  ultimo_login_em: string | null;
  foto_url: string | null;
  online: boolean;
}

export interface ActivityLogEntry {
  id: number;
  usuario_id: number | null;
  usuario_nome: string | null;
  usuario_email: string | null;
  acao: string;
  entidade: string | null;
  entidade_id: number | null;
  descricao: string | null;
  criado_em: string;
}

export interface MinhasMetricas {
  total_acoes: number;
  criacoes: number;
  edicoes: number;
  exclusoes: number;
  logins: number;
  ultimo_login_em: string | null;
}

export interface SetupInput {
  nome: string;
  email: string;
  senha: string;
}

export interface LoginInput {
  email: string;
  senha: string;
}

export interface ChangePasswordInput {
  senha_atual: string;
  senha_nova: string;
}

export interface CreateUsuarioInput {
  nome: string;
  email: string;
  senha: string;
  papel: Papel;
  grupos: GrupoChave[];
}

export type NivelIndicador = "indicador" | "apoiador" | "parceiro" | "embaixador" | "elite";

export interface NivelConfig {
  nivel: NivelIndicador;
  label: string;
  valor_fixo: number;
  percentual: number;
  ordem: number;
}

export type NivelConfigInput = Partial<Pick<NivelConfig, "label" | "valor_fixo" | "percentual">>;

// Comissão vigente: R$/kWh de geração esperada, por nível da cadeia de
// recrutamento (1 = quem indicou; 2 = quem recrutou o 1; 3 = quem recrutou o 2).
export interface ComissaoNivel {
  nivel: 1 | 2 | 3;
  valor_por_kwh: number;
}

// Negócio parado no estágio "Gerar Documentação" da Solarz — vira card na tela.
export interface NegocioPendente {
  solarz_deal_id: number;
  nome_negocio: string | null;
  valor_projeto: number | null;
  criado_em: string | null;
  ja_gerado: boolean;
}

export interface GeracaoDocumento {
  id: number;
  solarz_deal_id: number;
  cliente_id: number | null;
  cliente_nome: string | null;
  projeto_id: number | null;
  projeto_codigo: string | null;
  numero_pedido: string | null;
  numero_cft: string | null;
  status: "processando" | "pronto" | "erro";
  erro: string | null;
  pasta: string | null;
  arquivos: string[];
  criado_em: string;
  atualizado_em: string;
}

export interface Indicador {
  id: number;
  nome: string;
  email: string;
  telefone: string | null;
  codigo_indicacao: string;
  nivel: NivelIndicador;
  total_vendas: number;
  total_ganhos: number;
  criado_em: string;
  ultimo_login_em: string | null;
}

export type StatusIndicacao = "recebido" | "em_atendimento" | "negociacao" | "fechado" | "perdido" | "cancelado";
export type ResultadoIndicacao = "novo_contrato" | "em_andamento" | "sem_interesse" | "cancelado";

export interface Indicacao {
  id: number;
  indicador_id: number;
  indicador_nome?: string;
  indicador_codigo?: string;
  nome_indicado: string;
  telefone_indicado: string;
  cidade: string | null;
  conta_energia_estimada: number | null;
  nivel_interesse: "sim" | "talvez" | "nao_sei";
  observacoes: string | null;
  status: StatusIndicacao;
  setor: string | null;
  operador_id: number | null;
  valor_sistema: number | null;
  comissao_gerada: number | null;
  resultado: ResultadoIndicacao | null;
  tipo_contrato: string | null;
  criado_em: string;
  atualizado_em: string;
}

export interface IndicacaoUpdateInput {
  status?: StatusIndicacao;
  setor?: string;
  valor_sistema?: number;
  resultado?: ResultadoIndicacao;
  tipo_contrato?: string;
  observacoes?: string;
}

export interface ResumoIndicador {
  id: number;
  nome: string;
  codigo_indicacao: string;
  nivel: NivelIndicador;
  total_ganhos: number;
  total_indicacoes: number;
  em_andamento: number;
  fechados: number;
  cancelados: number;
}

export type StatusSuporteThread = "aberto" | "encerrado";

export interface SuporteThread {
  id: number;
  usuario_id: number;
  usuario_nome?: string;
  status: StatusSuporteThread;
  admin_usuario_id: number | null;
  criado_em: string;
  encerrado_em: string | null;
  ultima_mensagem?: string | null;
  ultima_mensagem_em?: string | null;
}

export interface SuporteMensagem {
  id: number;
  thread_id: number;
  autor_usuario_id: number;
  autor_nome: string;
  autor_papel: Papel;
  texto: string;
  criado_em: string;
}

export interface SuporteAvaliacao {
  id: number;
  thread_id: number;
  admin_usuario_id: number;
  positiva: boolean;
  comentario: string | null;
  criado_em: string;
}

export interface AvaliacoesSuporteResumo {
  total: number;
  positivas: number;
  negativas: number;
}
