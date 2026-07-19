# Usinas

Recurso: `Usina` — usina fotovoltaica instalada para um cliente.

## Modelo

| Campo | Tipo | Obrigatório | Observação |
|---|---|---|---|
| `id` | int | somente leitura | |
| `nome` | string | sim | ex: `"7DPRODUCOES"` |
| `cliente_id` | int | não | FK para `Cliente` (pode ser nulo se não identificado na planilha de origem) |
| `potencia_kwp` | float | sim | |
| `data_instalacao` | date | não | `YYYY-MM-DD` |
| `total_investido` | float | não | em R$ |
| `geracao_anual_esperada` | float | não | em kWh |
| `cep` | string | não | |
| `latitude` | float | não | |
| `longitude` | float | não | |
| `criado_em` | timestamp | somente leitura | |
| `atualizado_em` | timestamp | somente leitura | |

---

## `GET /api/v1/usinas`

### Query params opcionais
- `cliente_id`: filtra por cliente
- `nome`: busca por substring
- `potencia_min` / `potencia_max`: filtra por faixa de potência (kWp)

### Resposta 200
```json
{
  "data": [
    {
      "id": 1,
      "nome": "7DPRODUCOES",
      "cliente_id": null,
      "potencia_kwp": 6.54,
      "data_instalacao": "2022-09-28",
      "total_investido": 0,
      "geracao_anual_esperada": null,
      "cep": null,
      "latitude": null,
      "longitude": null,
      "criado_em": "2026-07-06T12:00:00Z",
      "atualizado_em": "2026-07-06T12:00:00Z"
    }
  ],
  "pagination": { "page": 1, "per_page": 20, "total_items": 101, "total_pages": 6 }
}
```

---

## `GET /api/v1/usinas/{id}`

### Resposta 200
Mesmo objeto do item acima.

### Resposta 404
```json
{ "error": { "code": "NOT_FOUND", "message": "Usina 999 não encontrada" } }
```

---

## `GET /api/v1/usinas/{id}/geracao`

Lista os registros de geração mensal da usina (mesmo formato de [`GET /geracao`](05_geracao.md), já filtrado por `usina_id`). Paginado.

### Query params opcionais
- `ano`: filtra por ano

---

## `POST /api/v1/usinas`

### Corpo da requisição
```json
{
  "nome": "PADARIA DINAMARCA",
  "cliente_id": null,
  "potencia_kwp": 67.2,
  "data_instalacao": "2020-09-08",
  "total_investido": 174625.43,
  "geracao_anual_esperada": 92400,
  "cep": "29902-435"
}
```

### Resposta 201
Mesmo formato do `GET /usinas/{id}`.

### Resposta 400
```json
{ "error": { "code": "VALIDATION_ERROR", "message": "Campo 'potencia_kwp' é obrigatório" } }
```

---

## `PUT /api/v1/usinas/{id}`

### Corpo da requisição
```json
{
  "nome": "PADARIA DINAMARCA",
  "cliente_id": null,
  "potencia_kwp": 67.2,
  "data_instalacao": "2020-09-08",
  "total_investido": 174625.43,
  "geracao_anual_esperada": 92400,
  "cep": "29902-435"
}
```

### Resposta 200
Usina atualizada, mesmo formato do `GET`.

---

## `PATCH /api/v1/usinas/{id}`

### Corpo da requisição (só os campos a alterar)
```json
{ "total_investido": 180000.00 }
```

### Resposta 200
Usina atualizada, mesmo formato do `GET`.

---

## `DELETE /api/v1/usinas/{id}`

Remove a usina e, em cascata, seus registros de geração.

### Resposta 204
Sem corpo.
