# Convenções da API

Base URL: `/api/v1`

## Paginação

Toda rota de listagem (`GET` de coleção) aceita:

| Query param | Tipo | Padrão | Observação |
|---|---|---|---|
| `page` | int | 1 | página atual (>= 1) |
| `per_page` | int | 20 | itens por página (1–100) |

Resposta de listagem sempre no formato:

```json
{
  "data": [ /* itens do recurso */ ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total_items": 137,
    "total_pages": 7
  }
}
```

## Erros

Todo erro segue o formato:

```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Cliente 123 não encontrado"
  }
}
```

Códigos usados:

| HTTP | code | quando |
|---|---|---|
| 400 | `VALIDATION_ERROR` | corpo da requisição inválido ou campo obrigatório ausente |
| 404 | `NOT_FOUND` | recurso ou recurso pai (ex: `cliente_id`) não existe |
| 409 | `CONFLICT` | violação de unicidade (ex: `codigo` de projeto duplicado) |

## PUT vs PATCH

- `PUT`: substitui o recurso inteiro — todos os campos obrigatórios devem ser enviados.
- `PATCH`: atualização parcial — envie somente os campos que quer alterar.

## Datas

Formato `YYYY-MM-DD` para datas, `YYYY-MM-DDTHH:MM:SSZ` (ISO 8601 UTC) para timestamps.

## Campos somente-leitura

`id`, `criado_em`, `atualizado_em` são gerados pelo servidor e ignorados se enviados no corpo de POST/PUT/PATCH.
