# Indicações (leads do app de indicações)

Recurso: `Indicacao` — lead cadastrado por um indicador. É a mesma entidade que aparece nas telas **Indicações** e **Atendimento** do CRM: o operador acompanha, muda o status/setor e, ao encerrar o atendimento, registra o resultado — o que gera a comissão do indicador.

Rotas nesse arquivo exigem login de usuário do CRM (`usuarios`, `session["user_id"]`) — não confundir com a sessão de indicador (`07_indicadores.md`).

## Modelo

| Campo | Tipo | Observação |
|---|---|---|
| `id` | int | somente leitura |
| `indicador_id` | int | FK, definido na criação (rota do indicador) |
| `nome_indicado`, `telefone_indicado` | string | dados do lead |
| `cidade` | string \| null | |
| `conta_energia_estimada` | float \| null | informado pelo indicador, só para triagem — não é o `valor_sistema` do contrato |
| `nivel_interesse` | string | `sim` \| `talvez` \| `nao_sei` |
| `observacoes` | string \| null | |
| `status` | string | `recebido` → `em_atendimento` → `negociacao` → `fechado` \| `perdido` \| `cancelado` |
| `setor` | string \| null | setor pra quem o atendimento foi transferido (Comercial, Financeiro, Suporte Técnico, ...) |
| `operador_id` | int \| null | FK `usuarios`, quem está/esteve atendendo |
| `valor_sistema` | float \| null | valor do contrato — só a Tecsol define, via `PATCH` |
| `comissao_gerada` | float \| null | **sempre calculada pelo servidor**, nunca aceita no body |
| `resultado` | string \| null | `novo_contrato` \| `em_andamento` \| `sem_interesse` \| `cancelado` — preenchido ao "Encerrar atendimento" |
| `tipo_contrato` | string \| null | |
| `criado_em`, `atualizado_em` | timestamp | |

---

## `GET /api/v1/indicacoes`
Paginado. Query params opcionais: `status`, `indicador_id`. Cada item inclui `indicador_nome` e `indicador_codigo` (join).

## `GET /api/v1/indicacoes/resumo`
Sem paginação — um resumo por indicador, para o dashboard da tela **Indicações**:
```json
{
  "data": [
    {
      "id": 1, "nome": "Fulano", "codigo_indicacao": "TECSOL-FULA248", "nivel": "parceiro",
      "total_ganhos": 1240.0,
      "total_indicacoes": 8, "em_andamento": 2, "fechados": 4, "cancelados": 2
    }
  ]
}
```

## `GET /api/v1/indicacoes/{id}`
200 → `Indicacao`. 404 se não existir.

## `PATCH /api/v1/indicacoes/{id}`
Campos aceitos: `status`, `setor`, `valor_sistema`, `resultado`, `tipo_contrato`, `observacoes`. Qualquer outro campo no body é ignorado (em especial `comissao_gerada` e `total_vendas`/`total_ganhos` do indicador — não são editáveis diretamente por ninguém).

```json
{ "status": "fechado", "valor_sistema": 32000, "resultado": "novo_contrato", "tipo_contrato": "Instalação de usina" }
```

Quando `status` muda **para** `"fechado"` (e só nessa transição):
1. `comissao_gerada` é calculada como `niveis_config.valor_fixo + valor_sistema * niveis_config.percentual`, usando o nível atual do indicador (tabela `niveis_config`, ver `07_indicadores.md`).
2. `indicadores.total_vendas` incrementa e `total_ganhos` soma a comissão.
3. O nível do indicador pode subir automaticamente (mesmas faixas do app original: 3 vendas → apoiador/parceiro, 5 → parceiro/embaixador, 10 → elite).

200 → `Indicacao` atualizada.
