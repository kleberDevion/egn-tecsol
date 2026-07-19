# Suporte (chat interno: operador ↔ admin)

Recurso: `SuporteThread` — uma conversa entre um usuário `operador` do CRM e o "suporte interno" (qualquer usuário `admin`). Todas as rotas exigem login de usuário do CRM (`session["user_id"]`).

## Modelo

**`SuporteThread`**

| Campo | Tipo | Observação |
|---|---|---|
| `id` | int | somente leitura |
| `usuario_id` | int | FK `usuarios`, o operador dono da conversa |
| `status` | string | `aberto` \| `encerrado` |
| `admin_usuario_id` | int \| null | quem encerrou a conversa (fica setado só depois de encerrada) |
| `criado_em`, `encerrado_em` | timestamp | |

**`SuporteMensagem`**

| Campo | Tipo | Observação |
|---|---|---|
| `id` | int | |
| `thread_id` | int | FK |
| `autor_usuario_id`, `autor_nome`, `autor_papel` | | quem escreveu (operador ou admin) |
| `texto` | string | |
| `criado_em` | timestamp | |

**`SuporteAvaliacao`** — uma por thread, só depois de encerrada, só quem abriu pode criar.

| Campo | Tipo | Observação |
|---|---|---|
| `id` | int | |
| `thread_id` | int | UNIQUE |
| `admin_usuario_id` | int | copiado do `thread.admin_usuario_id`, nunca vem do body |
| `positiva` | bool | |
| `comentario` | string \| null | |
| `criado_em` | timestamp | |

---

## `GET /api/v1/suporte/minha-thread`
Só operador (400 se admin). Retorna a conversa mais recente do usuário logado (`SuporteThread` ou `null` se nunca abriu uma).

## `GET /api/v1/suporte/threads?status=aberto`
Só admin (403 senão). Inbox: uma linha por conversa (mais recente primeiro), com `usuario_nome`, `ultima_mensagem`, `ultima_mensagem_em`. `status` é opcional.

## `GET /api/v1/suporte/threads/{id}/mensagens`
200 → `{ "data": [SuporteMensagem, ...] }`. Só o dono da thread ou um admin (403 senão).

## `POST /api/v1/suporte/mensagens`
```json
{ "texto": "..." }
```
- **Operador:** manda pra sua conversa mais recente; se ela não existe ou já está `encerrada`, uma nova é criada automaticamente (uma conversa "encerrada" nunca reabre — a próxima mensagem começa uma thread nova).
- **Admin:** precisa informar `thread_id` no body; 400 se a thread já estiver encerrada.

201 → `SuporteMensagem`, e emite `suporte:nova` via WebSocket (payload `{ thread_id, mensagem }`) pra sala do operador dono e pra sala `admins`.

## `POST /api/v1/suporte/threads/{id}/encerrar`
Só admin. 400 se já estiver encerrada. Seta `status=encerrado`, `admin_usuario_id` = quem encerrou. 200 → `SuporteThread` atualizada, e emite `suporte:encerrado` (payload = a thread) pra sala do operador dono, pra ele saber que pode avaliar.

## `GET /api/v1/suporte/threads/{id}/avaliacao`
Só o dono da thread ou um admin. 200 → `SuporteAvaliacao` ou `null` se ainda não foi avaliada (pra UI saber se deve mostrar o formulário depois de um reload).

## `POST /api/v1/suporte/threads/{id}/avaliacao`
Só o operador dono da thread (403 pra admin ou pra outro operador), só se `status=encerrado` (400 senão), uma vez só (409 se repetir).
```json
{ "positiva": true, "comentario": "opcional" }
```
201 → `SuporteAvaliacao`.

---

## `GET /api/v1/dashboard/avaliacoes-suporte`
Qualquer usuário logado. Agregado global — **nunca** identifica quem avaliou nem quebra por admin:
```json
{ "total": 12, "positivas": 9, "negativas": 3 }
```

## WebSocket

Todo usuário logado entra automaticamente (no `connect`) na sala `suporte:{seu_id}` (pra receber respostas na própria conversa) e, se for admin, também em `admins` (pra ver tudo que rola em qualquer conversa, sem precisar entrar sala por sala). Eventos: `suporte:nova` (nova mensagem), `suporte:encerrado` (thread fechada).
