# Clientes

Recurso: `Cliente` — pessoa física ou jurídica dona de um ou mais projetos/usinas.

## Modelo

| Campo | Tipo | Obrigatório | Observação |
|---|---|---|---|
| `id` | int | somente leitura | |
| `tipo` | string | sim | `"PF"` ou `"PJ"` |
| `nome` | string | sim | |
| `email` | string | não | |
| `telefone` | string | não | |
| `cpf_cnpj` | string | não | CPF (PF) ou CNPJ (PJ) |
| `endereco` | string | não | |
| `cep` | string | não | |
| `criado_em` | timestamp | somente leitura | |
| `atualizado_em` | timestamp | somente leitura | |

---

## `GET /api/v1/clientes`

Lista clientes, paginado (ver [convenções](00_convencoes.md)).

### Query params opcionais
- `nome`: filtro por substring (case-insensitive)
- `tipo`: `PF` ou `PJ`
- `cpf_cnpj`: busca exata

### Resposta 200

```json
{
  "data": [
    {
      "id": 1,
      "tipo": "PF",
      "nome": "Orly Rosse Pereira",
      "email": null,
      "telefone": null,
      "cpf_cnpj": null,
      "endereco": null,
      "cep": null,
      "criado_em": "2026-07-06T12:00:00Z",
      "atualizado_em": "2026-07-06T12:00:00Z"
    }
  ],
  "pagination": { "page": 1, "per_page": 20, "total_items": 24, "total_pages": 2 }
}
```

---

## `GET /api/v1/clientes/{id}`

### Resposta 200
```json
{
  "id": 1,
  "tipo": "PF",
  "nome": "Orly Rosse Pereira",
  "email": null,
  "telefone": null,
  "cpf_cnpj": null,
  "endereco": null,
  "cep": null,
  "criado_em": "2026-07-06T12:00:00Z",
  "atualizado_em": "2026-07-06T12:00:00Z"
}
```

### Resposta 404
```json
{ "error": { "code": "NOT_FOUND", "message": "Cliente 999 não encontrado" } }
```

---

## `POST /api/v1/clientes`

### Corpo da requisição
```json
{
  "tipo": "PF",
  "nome": "Kleber Nunes de Lacerda",
  "email": "kleber@example.com",
  "telefone": "27999990000",
  "cpf_cnpj": "12345678900",
  "endereco": "Rua X, 123",
  "cep": "29900-000"
}
```

### Resposta 201
Mesmo formato do `GET /clientes/{id}`, com `id`, `criado_em`, `atualizado_em` preenchidos.

### Resposta 400
```json
{ "error": { "code": "VALIDATION_ERROR", "message": "Campo 'nome' é obrigatório" } }
```

---

## `PUT /api/v1/clientes/{id}`

Substitui o cliente inteiro — envie todos os campos obrigatórios.

### Corpo da requisição
```json
{
  "tipo": "PF",
  "nome": "Kleber Nunes de Lacerda",
  "email": "novo-email@example.com",
  "telefone": "27999990000",
  "cpf_cnpj": "12345678900",
  "endereco": "Rua X, 123",
  "cep": "29900-000"
}
```

### Resposta 200
Cliente atualizado, mesmo formato do `GET`.

---

## `PATCH /api/v1/clientes/{id}`

### Corpo da requisição (só os campos a alterar)
```json
{ "email": "novo-email@example.com" }
```

### Resposta 200
Cliente atualizado, mesmo formato do `GET`.

---

## `DELETE /api/v1/clientes/{id}`

Remove o cliente. Falha com `409 CONFLICT` se houver projetos ou usinas vinculadas.

### Resposta 204
Sem corpo.

### Resposta 409
```json
{ "error": { "code": "CONFLICT", "message": "Cliente 1 possui projetos vinculados e não pode ser removido" } }
```
