# Geração

Recurso: `Geracao` — registro de geração de energia mensal de uma usina.

## Modelo

| Campo | Tipo | Obrigatório | Observação |
|---|---|---|---|
| `id` | int | somente leitura | |
| `usina_id` | int | sim | FK para `Usina` |
| `ano` | int | sim | ex: `2026` |
| `mes` | int | sim | `1`–`12` |
| `valor_kwh` | float | sim | |
| `criado_em` | timestamp | somente leitura | |
| `atualizado_em` | timestamp | somente leitura | |

Restrição: par (`usina_id`, `ano`, `mes`) é único.

---

## `GET /api/v1/geracao`

### Query params opcionais
- `usina_id`: filtra por usina
- `ano`: filtra por ano
- `mes`: filtra por mês (1–12)

### Resposta 200
```json
{
  "data": [
    {
      "id": 1,
      "usina_id": 1,
      "ano": 2026,
      "mes": 1,
      "valor_kwh": 654.69,
      "criado_em": "2026-07-06T12:00:00Z",
      "atualizado_em": "2026-07-06T12:00:00Z"
    }
  ],
  "pagination": { "page": 1, "per_page": 20, "total_items": 1200, "total_pages": 60 }
}
```

---

## `GET /api/v1/geracao/{id}`

### Resposta 200
Mesmo objeto do item acima.

### Resposta 404
```json
{ "error": { "code": "NOT_FOUND", "message": "Registro de geração 999 não encontrado" } }
```

---

## `POST /api/v1/geracao`

### Corpo da requisição
```json
{
  "usina_id": 1,
  "ano": 2026,
  "mes": 2,
  "valor_kwh": 654.69
}
```

### Resposta 201
Mesmo formato do `GET /geracao/{id}`.

### Resposta 404 (usina_id inexistente)
```json
{ "error": { "code": "NOT_FOUND", "message": "Usina 999 não encontrada" } }
```

### Resposta 409 (mês duplicado para a usina)
```json
{ "error": { "code": "CONFLICT", "message": "Já existe registro de geração para usina 1 em 2026-02" } }
```

---

## `PUT /api/v1/geracao/{id}`

### Corpo da requisição
```json
{
  "usina_id": 1,
  "ano": 2026,
  "mes": 2,
  "valor_kwh": 700.0
}
```

### Resposta 200
Registro atualizado, mesmo formato do `GET`.

---

## `PATCH /api/v1/geracao/{id}`

### Corpo da requisição (só os campos a alterar)
```json
{ "valor_kwh": 700.0 }
```

### Resposta 200
Registro atualizado, mesmo formato do `GET`.

---

## `DELETE /api/v1/geracao/{id}`

### Resposta 204
Sem corpo.
