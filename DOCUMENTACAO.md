# Tecsol — API + CRM

Documentação de tudo que foi construído a partir dos dados em `2026/` (pastas de projeto) e `DAVI/` (planilhas de monitoramento): uma API REST em Flask e um CRM em React para consumi-la.

```
tecsol/
  2026/          # dados de origem: pastas de projeto por cliente (não gerado por nós)
  DAVI/          # dados de origem: planilhas Excel (não gerado por nós)
  api/           # API REST em Flask + SQLite
  crm/           # CRM em React + TypeScript + TailwindCSS
```

---

## 1. API (`api/`)

### Stack
Python + Flask + SQLite (via `sqlite3`, sem ORM) + pandas/openpyxl só para o seed.

### Estrutura

```
api/
  schema.sql              # DDL das 6 tabelas
  seed_from_pandas.py      # popula tecsol.db a partir de 2026/ e DAVI/
  tecsol.db                 # banco gerado (SQLite)
  run.py                    # ponto de entrada (python run.py)
  requirements.txt
  app/
    __init__.py            # app factory, registra blueprints, CORS
    db.py                  # conexão SQLite por request (g), init_db
    errors.py              # ApiError + handlers (400/404/409)
    pagination.py          # paginate_query() e validação de page/per_page
    routes/
      clientes.py
      projetos.py
      documentos.py
      usinas.py
      geracao.py
      concessionarias.py
  contracts/               # contrato de cada rota (request/response em JSON)
    00_convencoes.md       # paginação, formato de erro, PUT vs PATCH
    01_clientes.md
    02_projetos.md
    03_documentos.md
    04_usinas.md
    05_geracao.md
    06_concessionarias.md
```

### Modelo de dados

| Tabela | Origem dos dados | Observação |
|---|---|---|
| `clientes` | nome extraído das 24 pastas `PJ-2026-...` em `2026/2026/` | `tipo` (PF/PJ) inferido por heurística de palavras-chave no nome |
| `projetos` | as próprias pastas `PJ-2026-...` | `codigo` = nome da pasta até o " - ", `pasta` = caminho relativo de origem |
| `documentos` | arquivos dentro de cada pasta de projeto | `categoria` = subpasta (`4_Contrato`, `9_Notas Fiscais`, etc.); metadados apenas — **o binário do arquivo não é servido pela API** |
| `usinas` | aba `Usinas` de `template_import_....xlsx` | 235 usinas; `cliente_id` fica `null` — a planilha não tem um vínculo confiável com os 24 clientes de projeto |
| `geracao` | aba `Geração` do mesmo arquivo | valores mensais; a planilha não indica o ano, então foi assumido `2026` para todos os registros (constante `ANO_REFERENCIA_GERACAO` em `seed_from_pandas.py`) |
| `concessionarias` | aba `Metadados`, coluna `Concessionárias` | lookup simples (nome único) |

**Dado sensível excluído de propósito:** as abas `Portais` e `Login concessionária` de `Dados - Monitoramento (1)...xlsx` continham usuário/senha em texto puro. Elas não têm nenhuma tabela, rota ou campo correspondente nesta API.

### Rodando a API

```bash
cd api
pip install -r requirements.txt
python seed_from_pandas.py   # popula/recria tecsol.db a partir dos dados de origem
python run.py                 # sobe em http://127.0.0.1:5000
```

`seed_from_pandas.py` é idempotente: recria o schema e re-popula do zero a cada execução (útil para resetar o banco depois de testes no Insomnia).

### Convenções da API

- Base: `/api/v1`
- Toda listagem é paginada via `?page=` e `?per_page=` (padrão 20, máx. 100), resposta no formato:
  ```json
  { "data": [...], "pagination": { "page": 1, "per_page": 20, "total_items": 24, "total_pages": 2 } }
  ```
- Erros sempre `{ "error": { "code": "...", "message": "..." } }` — códigos `VALIDATION_ERROR` (400), `NOT_FOUND` (404), `CONFLICT` (409).
- `PUT` substitui o recurso inteiro (todos os campos obrigatórios); `PATCH` atualiza só os campos enviados.
- CORS liberado (`Access-Control-Allow-Origin: *`) para uso local com o CRM ou ferramentas como o Insomnia.
- Detalhe de cada rota (payload de entrada/saída por verbo) está em `api/contracts/`.

### Rotas por recurso

| Recurso | Rotas |
|---|---|
| Clientes | `GET/POST /clientes`, `GET/PUT/PATCH/DELETE /clientes/{id}` |
| Projetos | `GET/POST /projetos`, `GET/PUT/PATCH/DELETE /projetos/{id}`, `GET /projetos/{id}/documentos` |
| Documentos | `GET/POST /documentos`, `GET/PUT/PATCH/DELETE /documentos/{id}` |
| Usinas | `GET/POST /usinas`, `GET/PUT/PATCH/DELETE /usinas/{id}`, `GET /usinas/{id}/geracao` |
| Geração | `GET/POST /geracao`, `GET/PUT/PATCH/DELETE /geracao/{id}` |
| Concessionárias | `GET/POST /concessionarias`, `GET/PUT/PATCH/DELETE /concessionarias/{id}` |

---

## 2. CRM (`crm/`)

### Stack
React 19 + TypeScript + Vite + TailwindCSS v4 + react-router-dom. Visual inspirado no Material Design do Google (Roboto, azul `#1a73e8`, cantos arredondados, cards com sombra leve).

### Estrutura

```
crm/src/
  types.ts               # interfaces TS espelhando os contratos da API
  api/
    client.ts             # fetch wrapper tipado + tratamento de erro (ApiError)
    resource.ts           # factory genérica de CRUD (list/get/create/replace/update/remove)
    clientes.ts, projetos.ts, documentos.ts, usinas.ts, geracao.ts, concessionarias.ts
  hooks/
    usePaginatedResource.ts  # estado de página/filtros/loading/erro para listagens
    useClientesLookup.ts     # cache simples de clientes para selects e exibir nome por id
  components/
    layout/                  # AppShell, Sidebar, TopBar
    ui/                       # Button, Modal, ConfirmDialog, Table, Pagination, Badge,
                               # Field (Input/Select), Spinner, EmptyState, ToastProvider
    icons.tsx                 # ícones SVG inline (sem dependência externa)
  pages/
    DashboardPage.tsx
    clientes/   ClientesPage.tsx, ClienteForm.tsx
    projetos/   ProjetosPage.tsx, ProjetoForm.tsx, ProjetoDetailPage.tsx, DocumentoForm.tsx
    usinas/     UsinasPage.tsx, UsinaForm.tsx, UsinaDetailPage.tsx, GeracaoForm.tsx
    concessionarias/  ConcessionariasPage.tsx, ConcessionariaForm.tsx
```

### Funcionalidades

- **Dashboard**: cards com totais reais de cada recurso (via `total_items` da paginação).
- **Clientes**: listagem paginada com busca por nome e filtro por tipo; criar/editar em modal; excluir com confirmação (bloqueado pela API com 409 se houver projeto/usina vinculada — o erro aparece como toast).
- **Projetos**: listagem com filtro por cliente e ano; ao clicar numa linha, abre o detalhe do projeto com a lista de documentos (criar/editar/excluir documento).
- **Usinas**: listagem com busca por nome; ao clicar, abre o detalhe com um gráfico de barras simples da geração mensal e a lista de registros de geração (criar/editar/excluir).
- **Concessionárias**: CRUD simples (nome único).
- Toda ação de escrita mostra um toast de sucesso ou erro (mensagem vinda diretamente do `error.message` da API).

### Rodando o CRM

```bash
cd crm
npm install
npm run dev   # http://localhost:5173
```

O Vite está configurado com proxy (`vite.config.ts`) de `/api` para `http://127.0.0.1:5000`, então o CRM espera a API rodando localmente na porta 5000. Basta abrir `http://localhost:5173` com a API no ar.

---

## 3. Decisões e observações importantes

- **`cliente_id` nulo em várias usinas**: a planilha de usinas não tem um vínculo confiável com os clientes dos projetos de 2026 — ficou como `null` de propósito (confirmado com o usuário).
- **Ano da geração mensal assumido como 2026**: a aba `Geração` da planilha não informa o ano por linha, só os valores por mês. Se isso precisar refletir anos diferentes por usina, o script `seed_from_pandas.py` precisa ser ajustado manualmente.
- **Heurística PF/PJ**: como a planilha não classifica os clientes, o tipo é inferido por palavras-chave no nome (ex: "MADEIREIRA", "LTDA", "BEACH" → PJ). Pode errar em nomes ambíguos — corrigível depois via `PATCH /clientes/{id}`.
- **Credenciais excluídas**: nenhuma senha das planilhas de origem foi importada, armazenada ou exposta em nenhum lugar desta API ou do CRM.
- **Documentos são só metadados**: a API nunca lê nem serve o conteúdo binário dos arquivos (PDF/DOCX/DWG); apenas nome, categoria, tamanho e caminho relativo de origem.
