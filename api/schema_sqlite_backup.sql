PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS clientes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo TEXT NOT NULL CHECK(tipo IN ('PF','PJ')),
    nome TEXT NOT NULL,
    email TEXT,
    telefone TEXT,
    cpf_cnpj TEXT,
    endereco TEXT,
    cep TEXT,
    criado_em TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    atualizado_em TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);

CREATE TABLE IF NOT EXISTS projetos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo TEXT NOT NULL UNIQUE,
    cliente_id INTEGER NOT NULL REFERENCES clientes(id),
    ano INTEGER NOT NULL,
    pasta TEXT,
    status TEXT NOT NULL DEFAULT 'ativo' CHECK(status IN ('ativo','cancelado','desistente')),
    criado_em TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    atualizado_em TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);

CREATE TABLE IF NOT EXISTS documentos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    projeto_id INTEGER NOT NULL REFERENCES projetos(id),
    categoria TEXT NOT NULL,
    nome_arquivo TEXT NOT NULL,
    extensao TEXT,
    tamanho_bytes INTEGER,
    caminho_relativo TEXT NOT NULL,
    criado_em TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    atualizado_em TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);

CREATE TABLE IF NOT EXISTS usinas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    cliente_id INTEGER REFERENCES clientes(id),
    potencia_kwp REAL NOT NULL,
    data_instalacao TEXT,
    total_investido REAL,
    geracao_anual_esperada REAL,
    cep TEXT,
    latitude REAL,
    longitude REAL,
    criado_em TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    atualizado_em TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);

CREATE TABLE IF NOT EXISTS geracao (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usina_id INTEGER NOT NULL REFERENCES usinas(id),
    ano INTEGER NOT NULL,
    mes INTEGER NOT NULL CHECK(mes BETWEEN 1 AND 12),
    valor_kwh REAL NOT NULL,
    criado_em TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    atualizado_em TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    UNIQUE(usina_id, ano, mes)
);

CREATE TABLE IF NOT EXISTS concessionarias (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL UNIQUE,
    criado_em TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    atualizado_em TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);

CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    senha_hash TEXT NOT NULL,
    papel TEXT NOT NULL CHECK(papel IN ('admin','operador')) DEFAULT 'operador',
    ativo INTEGER NOT NULL DEFAULT 1,
    foto_path TEXT,
    criado_em TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    atualizado_em TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    ultimo_login_em TEXT
);

-- Departamentos/áreas da empresa. Um usuário "operador" pode pertencer a um ou
-- mais grupos, que definem quais seções/ferramentas do CRM ele enxerga. Admin
-- sempre tem acesso a tudo, independente de grupo.
CREATE TABLE IF NOT EXISTS grupos (
    chave TEXT PRIMARY KEY,
    nome TEXT NOT NULL,
    ordem INTEGER NOT NULL DEFAULT 0
);

INSERT OR IGNORE INTO grupos (chave, nome, ordem) VALUES
    ('vendas',      'Vendas',            1),
    ('engenharia',  'Engenharia',        2),
    ('financeiro',  'Financeiro',        3),
    ('diretoria',   'CEO / Diretoria',   4),
    ('marketing',   'Marketing',         5),
    ('tecnologia',  'Tecnologia',        6);

CREATE TABLE IF NOT EXISTS usuario_grupos (
    usuario_id INTEGER NOT NULL REFERENCES usuarios(id),
    grupo_chave TEXT NOT NULL REFERENCES grupos(chave),
    PRIMARY KEY (usuario_id, grupo_chave)
);

CREATE TABLE IF NOT EXISTS activity_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER REFERENCES usuarios(id),
    acao TEXT NOT NULL,
    entidade TEXT,
    entidade_id INTEGER,
    descricao TEXT,
    criado_em TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);

CREATE TABLE IF NOT EXISTS configuracoes (
    chave TEXT PRIMARY KEY,
    valor TEXT NOT NULL
);

INSERT OR IGNORE INTO configuracoes (chave, valor) VALUES ('max_admin_contas', '5');

-- App de indicações (parceiros externos que indicam clientes à Tecsol)

CREATE TABLE IF NOT EXISTS niveis_config (
    nivel TEXT PRIMARY KEY,
    label TEXT NOT NULL,
    valor_fixo REAL NOT NULL DEFAULT 0,
    percentual REAL NOT NULL DEFAULT 0,
    ordem INTEGER NOT NULL DEFAULT 0
);

INSERT OR IGNORE INTO niveis_config (nivel, label, valor_fixo, percentual, ordem) VALUES
    ('indicador',  'Indicador',  200, 0.02, 1),
    ('apoiador',   'Apoiador',   300, 0.03, 2),
    ('parceiro',   'Parceiro',   400, 0.04, 3),
    ('embaixador', 'Embaixador', 500, 0.05, 4),
    ('elite',      'Elite',      700, 0.07, 5);

-- `recrutado_por_id` é a cadeia de quem recrutou quem pro programa de
-- parceiros (não confundir com quem indicou um cliente): sobe essa cadeia
-- pra pagar a comissão multi-nível por kWh (nível 1/2/3, ver app/solarz.py).
CREATE TABLE IF NOT EXISTS indicadores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    telefone TEXT,
    senha_hash TEXT NOT NULL,
    codigo_indicacao TEXT NOT NULL UNIQUE,
    recrutado_por_id INTEGER REFERENCES indicadores(id),
    nivel TEXT NOT NULL DEFAULT 'indicador' REFERENCES niveis_config(nivel),
    total_vendas INTEGER NOT NULL DEFAULT 0,
    total_ganhos REAL NOT NULL DEFAULT 0,
    ativo INTEGER NOT NULL DEFAULT 1,
    criado_em TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    atualizado_em TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    ultimo_login_em TEXT
);

CREATE TABLE IF NOT EXISTS indicacoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    indicador_id INTEGER NOT NULL REFERENCES indicadores(id),
    nome_indicado TEXT NOT NULL,
    telefone_indicado TEXT NOT NULL,
    cidade TEXT,
    conta_energia_estimada REAL,
    nivel_interesse TEXT NOT NULL DEFAULT 'nao_sei' CHECK(nivel_interesse IN ('sim','talvez','nao_sei')),
    observacoes TEXT,
    status TEXT NOT NULL DEFAULT 'recebido'
        CHECK(status IN ('recebido','em_atendimento','negociacao','fechado','perdido','cancelado')),
    setor TEXT,
    operador_id INTEGER REFERENCES usuarios(id),
    valor_sistema REAL,
    comissao_gerada REAL,
    resultado TEXT CHECK(resultado IN ('novo_contrato','em_andamento','sem_interesse','cancelado')),
    tipo_contrato TEXT,
    chat_token TEXT UNIQUE DEFAULT (lower(hex(randomblob(16)))),
    solarz_deal_id INTEGER,
    criado_em TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    atualizado_em TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);

-- Um registro por acesso ao link público de indicação (/i/{codigo}), pra
-- estatística de "cliques" no app do indicador — independe de a pessoa ter
-- preenchido o formulário ou não.
CREATE TABLE IF NOT EXISTS indicador_cliques (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    indicador_id INTEGER NOT NULL REFERENCES indicadores(id),
    criado_em TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);

-- Leads do site institucional (tecsolengenharia.com.br). Ficam FORA de
-- `indicacoes` de propósito: não são indicação de ninguém, não têm indicador
-- e nunca geram comissão — só viram negócio no funil Comercial - Pré-vendas.
CREATE TABLE IF NOT EXISTS leads_site (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    telefone TEXT NOT NULL,
    email TEXT,
    cidade TEXT,
    tipo_solucao TEXT,
    valor_conta TEXT,
    mensagem TEXT,
    origem TEXT,
    pagina TEXT,
    solarz_deal_id INTEGER,
    criado_em TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);

-- Comissão multi-nível por kWh de geração esperada (regra do dono do app):
-- nível 1 = quem indicou o cliente; nível 2 = quem recrutou o nível 1;
-- nível 3 = quem recrutou o nível 2 (cadeia indicadores.recrutado_por_id).
-- Valores em R$/kWh, editáveis pelo admin.
CREATE TABLE IF NOT EXISTS comissao_niveis (
    nivel INTEGER PRIMARY KEY CHECK(nivel IN (1,2,3)),
    valor_por_kwh REAL NOT NULL
);
INSERT OR IGNORE INTO comissao_niveis (nivel, valor_por_kwh) VALUES
    (1, 0.40), (2, 0.15), (3, 0.075);

-- Extrato de comissões pagas por indicação fechada: uma linha por beneficiário
-- (até 3 por venda, um por nível da cadeia de recrutamento).
CREATE TABLE IF NOT EXISTS comissoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    indicacao_id INTEGER NOT NULL REFERENCES indicacoes(id),
    indicador_id INTEGER NOT NULL REFERENCES indicadores(id),
    nivel INTEGER NOT NULL CHECK(nivel IN (1,2,3)),
    kwh REAL NOT NULL,
    valor_por_kwh REAL NOT NULL,
    valor REAL NOT NULL,
    criado_em TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);
CREATE INDEX IF NOT EXISTS idx_comissoes_indicacao ON comissoes(indicacao_id);
CREATE INDEX IF NOT EXISTS idx_comissoes_indicador ON comissoes(indicador_id);

-- Chat de uma indicação: entre quem clicou no link do indicador ("cliente", sem login,
-- identificado só pelo chat_token acima) e o operador do CRM que está atendendo.
CREATE TABLE IF NOT EXISTS mensagens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    indicacao_id INTEGER NOT NULL REFERENCES indicacoes(id),
    autor_tipo TEXT NOT NULL CHECK(autor_tipo IN ('cliente','operador','sistema')),
    autor_usuario_id INTEGER REFERENCES usuarios(id),
    texto TEXT NOT NULL,
    criado_em TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);

CREATE INDEX IF NOT EXISTS idx_projetos_cliente ON projetos(cliente_id);
CREATE INDEX IF NOT EXISTS idx_documentos_projeto ON documentos(projeto_id);
CREATE INDEX IF NOT EXISTS idx_usinas_cliente ON usinas(cliente_id);
CREATE INDEX IF NOT EXISTS idx_geracao_usina ON geracao(usina_id);
CREATE INDEX IF NOT EXISTS idx_activity_usuario ON activity_log(usuario_id);
CREATE INDEX IF NOT EXISTS idx_activity_criado ON activity_log(criado_em);
CREATE INDEX IF NOT EXISTS idx_indicacoes_indicador ON indicacoes(indicador_id);
CREATE INDEX IF NOT EXISTS idx_indicacoes_status ON indicacoes(status);
CREATE INDEX IF NOT EXISTS idx_mensagens_indicacao ON mensagens(indicacao_id);

-- Chat de suporte interno: conversas entre um operador e "suporte" (qualquer
-- admin pode ver/responder; o operador só vê as próprias). Cada conversa tem
-- início/fim: admin encerra, e aí o operador é convidado a avaliar quem atendeu.
CREATE TABLE IF NOT EXISTS suporte_threads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER NOT NULL REFERENCES usuarios(id),
    status TEXT NOT NULL DEFAULT 'aberto' CHECK(status IN ('aberto','encerrado')),
    admin_usuario_id INTEGER REFERENCES usuarios(id),
    criado_em TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    encerrado_em TEXT
);

CREATE TABLE IF NOT EXISTS suporte_mensagens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    thread_id INTEGER NOT NULL REFERENCES suporte_threads(id),
    autor_usuario_id INTEGER NOT NULL REFERENCES usuarios(id),
    texto TEXT NOT NULL,
    criado_em TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);

-- Avaliação do operador sobre o admin que o atendeu, feita depois que a
-- conversa é encerrada. Uma por thread. Nunca exposta com o autor (operador)
-- identificável nas métricas agregadas (ver dashboard) — só o total e o
-- positiva/negativa.
CREATE TABLE IF NOT EXISTS suporte_avaliacoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    thread_id INTEGER NOT NULL UNIQUE REFERENCES suporte_threads(id),
    admin_usuario_id INTEGER NOT NULL REFERENCES usuarios(id),
    positiva INTEGER NOT NULL CHECK(positiva IN (0,1)),
    comentario TEXT,
    criado_em TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);

CREATE INDEX IF NOT EXISTS idx_suporte_threads_usuario ON suporte_threads(usuario_id);
CREATE INDEX IF NOT EXISTS idx_suporte_mensagens_thread ON suporte_mensagens(thread_id);
