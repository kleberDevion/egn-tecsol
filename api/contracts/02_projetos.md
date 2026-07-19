# Projetos

Recurso: `Projeto` — uma pasta de caso de instalação (ex: `PJ-2026-1001-750-001-A`), vinculada a um cliente.

## Modelo

| Campo | Tipo | Obrigatório | Observação |
|---|---|---|---|
| `id` | int | somente leitura | |
| `codigo` | string | sim | único, ex: `"PJ-2026-1001-750-001-A"` |
| `cliente_id` | int | sim | FK para `Cliente` |
| `ano` | int | sim | ano do projeto, ex: `2026` |
| `pasta` | string | não | caminho relativo da pasta de origem |
| `criado_em` | timestamp | somente leitura | |
| `atualizado_em` | timestamp | somente leitura | |

---

## `GET /api/v1/projetos`

### Query params opcionais
- `cliente_id`: filtra por cliente
- `ano`: filtra por ano
- `codigo`: busca exata ou por substring

### Resposta 200
```json
{
  "data": [
    {
      "id": 1,
      "codigo": "PJ-2026-1001-750-001-A",
      "cliente_id": 1,
      "ano": 2026,
      "pasta": "2026/2026/PJ-2026-1001-750-001-A - Orly Rosse Pereira",
      "criado_em": "2026-07-06T12:00:00Z",
      "atualizado_em": "2026-07-06T12:00:00Z"
    }
  ],
  "pagination": { "page": 1, "per_page": 20, "total_items": 24, "total_pages": 2 }
}
```

---

## `GET /api/v1/projetos/{id}`

### Resposta 200
```json
{
  "id": 1,
  "codigo": "PJ-2026-1001-750-001-A",
  "cliente_id": 1,
  "ano": 2026,
  "pasta": "2026/2026/PJ-2026-1001-750-001-A - Orly Rosse Pereira",
  "criado_em": "2026-07-06T12:00:00Z",
  "atualizado_em": "2026-07-06T12:00:00Z"
}
```

### Resposta 404
```json
{ "error": { "code": "NOT_FOUND", "message": "Projeto 999 não encontrado" } }
```

---

## `GET /api/v1/projetos/{id}/documentos`

Lista documentos vinculados ao projeto (mesmo formato de [`GET /documentos`](03_documentos.md), já filtrado por `projeto_id`). Paginado.

---

## `POST /api/v1/projetos`

### Corpo da requisição
```json
{
  "codigo": "PJ-2026-1050-750-001-A",
  "cliente_id": 1,
  "ano": 2026,
  "pasta": "2026/2026/PJ-2026-1050-750-001-A - Novo Cliente"
}
```

### Resposta 201
Mesmo formato do `GET /projetos/{id}`.

### Resposta 400
```json
{ "error": { "code": "VALIDATION_ERROR", "message": "Campo 'codigo' é obrigatório" } }
```

### Resposta 404 (cliente_id inexistente)
```json
{ "error": { "code": "NOT_FOUND", "message": "Cliente 999 não encontrado" } }
```

### Resposta 409 (código duplicado)
```json
{ "error": { "code": "CONFLICT", "message": "Já existe um projeto com o código 'PJ-2026-1050-750-001-A'" } }
```

---

## `PUT /api/v1/projetos/{id}`

### Corpo da requisição
```json
{
  "codigo": "PJ-2026-1050-750-001-A",
  "cliente_id": 1,
  "ano": 2026,
  "pasta": "2026/2026/PJ-2026-1050-750-001-A - Novo Cliente"
}
```

### Resposta 200
Projeto atualizado, mesmo formato do `GET`.

---

## `PATCH /api/v1/projetos/{id}`

### Corpo da requisição (só os campos a alterar)
```json
{ "ano": 2027 }
```

### Resposta 200
Projeto atualizado, mesmo formato do `GET`.

---

## `DELETE /api/v1/projetos/{id}`

Remove o projeto e, em cascata, seus documentos.

### Resposta 204
Sem corpo.
