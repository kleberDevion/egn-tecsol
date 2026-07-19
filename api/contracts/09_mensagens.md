# Mensagens (chat de uma indicação)

Recurso: `Mensagem` — troca de mensagens dentro de **uma indicação específica**, entre a pessoa que clicou no link de indicação do parceiro ("cliente", sem login em nenhum dos dois apps) e o operador do CRM que está atendendo. Não é um chat entre o indicador e o operador — o indicador não participa dessa conversa.

**Ainda em aberto (fora deste contrato):** como exatamente o clique no link do indicador leva até esse chat (página pública, formulário antes, etc.) depende de mudanças em `app-indicacoes` que ainda não foram definidas. Este contrato cobre só o back-end: a conversa já existe amarrada a uma `indicacao` existente (via `chat_token`); a parte de "como o cliente chega no token" fica para quando isso for decidido.

## Modelo

| Campo | Tipo | Observação |
|---|---|---|
| `id` | int | somente leitura |
| `indicacao_id` | int | FK — só existe no lado autenticado do CRM (`08_indicacoes.md`); omitido nas respostas públicas |
| `autor_tipo` | string | `cliente` \| `operador` \| `sistema` |
| `autor_usuario_id` | int \| null | FK `usuarios`, só quando `autor_tipo = "operador"`; omitido nas respostas públicas |
| `texto` | string | |
| `criado_em` | timestamp | |

Cada `indicacao` ganha um `chat_token` (string aleatória de 32 hex, gerada automaticamente na criação — ver `08_indicacoes.md`) que funciona como a "senha" de acesso àquela conversa específica para quem não tem login. **Não é sequencial e não deve ser adivinhável** — por isso as rotas públicas usam `chat_token` na URL, nunca o `id` numérico da indicação.

---

## Lado CRM (autenticado como usuário — `session["user_id"]`)

## `GET /api/v1/indicacoes/{id}/mensagens`
200 → `{ "data": [Mensagem, ...] }`, ordenado por `criado_em`. 404 se a indicação não existir.

## `POST /api/v1/indicacoes/{id}/mensagens`
```json
{ "texto": "Oi! Vi que você se interessou por energia solar, posso ajudar?" }
```
`autor_tipo` sempre `"operador"`, `autor_usuario_id` sempre o usuário logado — nenhum dos dois vem do body. 201 → `Mensagem` criada, e a mensagem é emitida via WebSocket (`mensagem:nova`, ver abaixo) pra quem estiver com a sala aberta.

---

## Lado público (sem login — `chat_token` na URL)

## `GET /api/v1/publico/indicacoes/{chat_token}`
Contexto mínimo pro widget renderizar antes de carregar as mensagens: `{ "nome_indicado": "...", "status": "...", "criado_em": "..." }`. 404 se o token não existir.

## `GET /api/v1/publico/indicacoes/{chat_token}/mensagens`
200 → `{ "data": [...] }` — mesma forma de `Mensagem`, mas **sem** `indicacao_id` nem `autor_usuario_id` (não expõe IDs internos a um visitante anônimo).

## `POST /api/v1/publico/indicacoes/{chat_token}/mensagens`
```json
{ "texto": "Oi, quero saber mais" }
```
`autor_tipo` sempre `"cliente"`. 201 → `Mensagem` criada (mesmo formato do GET acima).

---

## WebSocket (Flask-SocketIO, já existente em `api/app/socket.py`)

- Conexão anônima agora é permitida (antes, `connect` recusava quem não tinha sessão de usuário do CRM — isso só afetava presença online/offline, que continua exigindo login).
- Evento `join_indicacao`, emitido pelo cliente do socket após conectar:
  ```json
  { "indicacao_id": 4 }        // operador logado no CRM
  ```
  ```json
  { "chat_token": "a1b2c3..." } // widget público, sem login
  ```
  Entra na sala `indicacao:{id}` correspondente — o servidor resolve `chat_token` → `id` e nunca deixa a sala vazar pra quem não sabe o token certo.
- Evento `mensagem:nova`, emitido pelo servidor pra sala `indicacao:{id}` toda vez que uma `Mensagem` é criada (por qualquer um dos dois lados acima) — payload é o mesmo objeto `Mensagem` retornado pelo POST.

## Segurança

- `id` numérico de indicação é sequencial e nunca é aceito/exposto nas rotas públicas — só `chat_token` (aleatório, 16 bytes).
- Rotas públicas nunca retornam `autor_usuario_id` nem `indicacao_id`.
- Não há como um visitante anônimo listar indicações ou descobrir tokens — precisa já ter o link/token em mãos.
