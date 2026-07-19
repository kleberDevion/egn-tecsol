# Indicadores (app de indicações)

Recurso: `Indicador` — parceiro externo que indica clientes à Tecsol pelo app de indicações. É uma identidade separada dos `usuarios` do CRM: login próprio, sessão própria (`session["indicador_id"]`), sem acesso ao CRM.

## Modelo

| Campo | Tipo | Observação |
|---|---|---|
| `id` | int | somente leitura |
| `nome` | string | |
| `email` | string | único |
| `telefone` | string \| null | |
| `codigo_indicacao` | string | gerado no signup, ex: `"TECSOL-FULA248"`, único |
| `nivel` | string | `indicador` \| `apoiador` \| `parceiro` \| `embaixador` \| `elite` — sobe automaticamente conforme vendas fechadas |
| `total_vendas` | int | só muda via `PATCH /indicacoes/{id}` no CRM quando o status vira `fechado` |
| `total_ganhos` | float | soma de todas as comissões geradas — **somente leitura pelo indicador**, nunca aceito em nenhum body |
| `criado_em`, `ultimo_login_em` | timestamp | |

`senha_hash` nunca é retornado.

---

## `POST /api/v1/indicadores/auth/signup`
```json
{ "nome": "Fulano", "email": "fulano@ex.com", "telefone": "27999990000", "senha": "Segredo123" }
```
201 → objeto `Indicador`, sessão iniciada. 409 se e-mail já existir.

## `POST /api/v1/indicadores/auth/login`
```json
{ "email": "fulano@ex.com", "senha": "Segredo123" }
```
200 → `Indicador`. 401 se credenciais inválidas.

## `POST /api/v1/indicadores/auth/logout`
204, exige sessão de indicador ativa.

## `GET /api/v1/indicadores/me`
200 → `Indicador` da sessão atual.

## `GET /api/v1/indicadores/minhas-indicacoes`
Paginado (`?page=&per_page=`). Só retorna leads do próprio indicador logado.

## `POST /api/v1/indicadores/indicacoes`
Cria um novo lead (o formulário "nova indicação" do app). `indicador_id` vem da sessão.
```json
{
  "nome_indicado": "Cliente X",
  "telefone_indicado": "27988887777",
  "cidade": "Vitória",
  "conta_energia_estimada": 450,
  "nivel_interesse": "sim",
  "observacoes": "..."
}
```
201 → objeto `Indicacao`, `status` sempre `"recebido"`.

**Importante:** `valor_sistema` e `comissao_gerada` não são campos aceitos nesta rota — mesmo que enviados no body, são ignorados. Só a Tecsol define esses valores, via `PATCH /api/v1/indicacoes/{id}` (contrato em `08_indicacoes.md`), autenticado como usuário do CRM.

## `PATCH /api/v1/indicadores/indicacoes/{id}`
O indicador pode acompanhar o próprio lead e atualizar o `status` (não substitui o atendimento da Tecsol, só reflete o que ele sabe/combinou com o cliente). Só a própria `indicacao` do indicador logado (404 se pertencer a outro).
```json
{ "status": "negociacao" }
```
`status` deve ser um de `recebido`, `em_atendimento`, `negociacao`, `perdido`, `cancelado` — **nunca `"fechado"`**: essa transição envolve `valor_sistema`/`comissao_gerada` e só é confirmada pela Tecsol via `PATCH /api/v1/indicacoes/{id}`.

200 → `Indicacao` atualizada.

## `GET /api/v1/indicadores`
Só admin (usuário do CRM). Paginado. Lista todos os parceiros cadastrados, para o painel de administração (`nome`, `email`, `codigo_indicacao`, `nivel`, `total_vendas`, `total_ganhos`, etc.).
