# Documentos

Recurso: `Documento` — metadados de um arquivo (PDF, DOCX, DWG, etc.) dentro da pasta de um projeto. **O conteúdo binário do arquivo não é servido pela API**, apenas metadados e o caminho relativo de origem.

## Modelo

| Campo | Tipo | Obrigatório | Observação |
|---|---|---|---|
| `id` | int | somente leitura | |
| `projeto_id` | int | sim | FK para `Projeto` |
| `categoria` | string | sim | nome da subpasta de origem, ex: `"4_Contrato"` (ver categorias conhecidas abaixo) |
| `nome_arquivo` | string | sim | ex: `"CT-2026-1001-750-001-A_Orly Rosse Pereira.docx"` |
| `extensao` | string | não | derivada de `nome_arquivo` se omitida, ex: `"docx"` |
| `tamanho_bytes` | int | não | |
| `caminho_relativo` | string | sim | caminho relativo à raiz de dados, ex: `"2026/2026/PJ-2026-1001-750-001-A - Orly Rosse Pereira/4_Contrato/CT-....docx"` |
| `criado_em` | timestamp | somente leitura | |
| `atualizado_em` | timestamp | somente leitura | |

### Categorias conhecidas (não é uma lista fechada)
`1_Orçamento`, `2_Memorial de Calculo`, `3_Memorial Descritivo`, `4_Contrato`, `5_Procuração`, `6_Concessionaria`, `7_Conselho de Classe`, `8_Conta de Energia`, `9_Notas Fiscais`, `10_Doc. Cliente`, `11_Relatório Fotográfico`, `12_Recibos`, `13_Banco`

---

## `GET /api/v1/documentos`

### Query params opcionais
- `projeto_id`: filtra por projeto
- `categoria`: filtra por categoria exata
- `extensao`: filtra por extensão (ex: `pdf`)

### Resposta 200
```json
{
  "data": [
    {
      "id": 10,
      "projeto_id": 1,
      "categoria": "4_Contrato",
      "nome_arquivo": "CT-2026-1001-750-001-A_Orly Rosse Pereira.docx",
      "extensao": "docx",
      "tamanho_bytes": 48231,
      "caminho_relativo": "2026/2026/PJ-2026-1001-750-001-A - Orly Rosse Pereira/4_Contrato/CT-2026-1001-750-001-A_Orly Rosse Pereira.docx",
      "criado_em": "2026-07-06T12:00:00Z",
      "atualizado_em": "2026-07-06T10:14:00Z"
    }
  ],
  "pagination": { "page": 1, "per_page": 20, "total_items": 312, "total_pages": 16 }
}
```

---

## `GET /api/v1/documentos/{id}`

### Resposta 200
Mesmo objeto do item acima.

### Resposta 404
```json
{ "error": { "code": "NOT_FOUND", "message": "Documento 999 não encontrado" } }
```

---

## `POST /api/v1/documentos`

Registra os metadados de um novo documento (não faz upload de arquivo).

### Corpo da requisição
```json
{
  "projeto_id": 1,
  "categoria": "9_Notas Fiscais",
  "nome_arquivo": "NF-00123.pdf",
  "tamanho_bytes": 102400,
  "caminho_relativo": "2026/2026/PJ-2026-1001-750-001-A - Orly Rosse Pereira/9_Notas Fiscais/NF-00123.pdf"
}
```

### Resposta 201
Mesmo formato do `GET /documentos/{id}`.

### Resposta 404 (projeto_id inexistente)
```json
{ "error": { "code": "NOT_FOUND", "message": "Projeto 999 não encontrado" } }
```

---

## `PUT /api/v1/documentos/{id}`

### Corpo da requisição
```json
{
  "projeto_id": 1,
  "categoria": "9_Notas Fiscais",
  "nome_arquivo": "NF-00123-v2.pdf",
  "tamanho_bytes": 110592,
  "caminho_relativo": "2026/2026/PJ-2026-1001-750-001-A - Orly Rosse Pereira/9_Notas Fiscais/NF-00123-v2.pdf"
}
```

### Resposta 200
Documento atualizado, mesmo formato do `GET`.

---

## `PATCH /api/v1/documentos/{id}`

### Corpo da requisição (só os campos a alterar)
```json
{ "categoria": "12_Recibos" }
```

### Resposta 200
Documento atualizado, mesmo formato do `GET`.

---

## `DELETE /api/v1/documentos/{id}`

Remove apenas o registro de metadados (não apaga arquivo em disco).

### Resposta 204
Sem corpo.
