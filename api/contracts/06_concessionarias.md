# Concessionárias

Recurso: `Concessionaria` — tabela de apoio com as distribuidoras de energia (concessionárias), usada como referência por outros recursos.

## Modelo

| Campo | Tipo | Obrigatório | Observação |
|---|---|---|---|
| `id` | int | somente leitura | |
| `nome` | string | sim | único, ex: `"AME"` |
| `criado_em` | timestamp | somente leitura | |
| `atualizado_em` | timestamp | somente leitura | |

> Nota de segurança: as planilhas de origem continham abas de credenciais (`Portais`, `Login concessionária`) com usuário/senha em texto puro. Essas informações foram **deliberadamente excluídas** do modelo de dados e da API — não existe nenhuma rota que exponha essas senhas.

---

## `GET /api/v1/concessionarias`

### Resposta 200
```json
{
  "data": [
    { "id": 1, "nome": "AME", "criado_em": "2026-07-06T12:00:00Z", "atualizado_em": "2026-07-06T12:00:00Z" }
  ],
  "pagination": { "page": 1, "per_page": 20, "total_items": 5, "total_pages": 1 }
}
```

---

## `GET /api/v1/concessionarias/{id}`

### Resposta 200
Mesmo objeto do item acima.

### Resposta 404
```json
{ "error": { "code": "NOT_FOUND", "message": "Concessionária 999 não encontrada" } }
```

---

## `POST /api/v1/concessionarias`

### Corpo da requisição
```json
{ "nome": "EDP" }
```

### Resposta 201
Mesmo formato do `GET /concessionarias/{id}`.

### Resposta 409 (nome duplicado)
```json
{ "error": { "code": "CONFLICT", "message": "Já existe concessionária com o nome 'EDP'" } }
```

---

## `PUT /api/v1/concessionarias/{id}`

### Corpo da requisição
```json
{ "nome": "EDP ES" }
```

### Resposta 200
Concessionária atualizada, mesmo formato do `GET`.

---

## `PATCH /api/v1/concessionarias/{id}`

### Corpo da requisição
```json
{ "nome": "EDP ES" }
```

### Resposta 200
Concessionária atualizada, mesmo formato do `GET`.

---

## `DELETE /api/v1/concessionarias/{id}`

### Resposta 204
Sem corpo.
