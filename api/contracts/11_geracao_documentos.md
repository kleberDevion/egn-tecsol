# Geração de Documentação (rascunho pra validação)

Fluxo 100% **pull**: ninguém envia dados pra gente. O egn-tecsol **busca** na
API da Solarz (mesma API key já usada pelo sync de indicações) os negócios que
chegaram no stage **"Gerar Documentação"** (id 51691, funil Comercial -
Vendas) e monta os cards da tela. Ao clicar em gerar, o servidor busca de novo
os dados completos (pessoa, negócio, proposta) e preenche os templates.
Nenhuma integração nova é criada (Fortlev é acesso interno da Tecsol; os dados
de equipamento entram na proposta da Solarz, e é de lá que leremos quando a
API expuser — ver "fontes pendentes" abaixo).

Regra de cliente (definida pelo dono): o trabalho da Tecsol não é recorrente.
Se já existir cliente com mesmo **nome + CPF**, NÃO cria outro — só adiciona
um novo contrato/projeto ao registro existente.

## `GET /api/v1/geracao-documentos/pendentes`
Busca na Solarz os negócios no stage "Gerar Documentação" e retorna os cards:
```json
{
  "data": [
    {
      "solarz_deal_id": 515,
      "cliente_nome": "Leandro dos Reis",
      "cliente_cpf": "13320018744",
      "valor_projeto": 21500.0,
      "ja_gerado": false
    }
  ]
}
```

## `POST /api/v1/geracao-documentos`
Dispara a geração pra um negócio — **um clique gera TUDO** (memorial,
contrato, procuração, RT e DWG de uma vez; o foco é agilidade, não há seleção
de documentos).

Ao clicar no card de um negócio em espera, abre um **form com dois campos**:
- **CFT** — o número vem do site de engenharia do governo, gerado manualmente
  pelo engenheiro (o site é cheio de puzzles/captcha, impossível automatizar);
- **Número de pedido** — sequencial começando em `01` e subindo (`02`, `03`,
  ...); o form já vem preenchido com o próximo da sequência, mas o operador
  pode ajustar. A numeração alimenta os códigos no padrão "N°..." da planilha:
  `#N° DOC TECSOL` = `{ano}-{seq}-750-001-A` e derivados
  `CT-{...}` (contrato), `MD-{...}` (memorial), `PJ-{...}` (projeto),
  `DE-{...}` (desenho) — ex: seq 1035 → `PJ-2026-1035-750-001-A`.

```json
{ "solarz_deal_id": 515, "numero_cft": "CFT2605857078", "numero_pedido": "07" }
```

### Resposta 202
```json
{
  "geracao_id": 17,
  "projeto_codigo": "PJ-2026-1042-750-001-A",
  "cliente_id": 31,
  "cliente_reaproveitado": true,
  "status": "processando"
}
```
Geração roda em background (Dramatiq). O card mostra
"Geração de documentos - Cliente {nome}" com o status; quando `pronto`, os 5
arquivos ficam numa pasta pro operador baixar e anexar na Solarz.

## `GET /api/v1/geracao-documentos` / `/{id}`
Lista/consulta gerações: `processando` | `pronto` | `erro` + arquivos gerados
(URLs de download).

---

## De onde vem cada variável dos templates

Variáveis = colunas reais do `CONTROLE PROJETOS ENGENHARIA _0307.xlsm`
(LINHA BASE / ART / Planilha1).

### Com fonte confirmada na API da Solarz (testado em deals reais)
| Variável do template | Fonte Solarz |
|---|---|
| `#NOME PF` / `#cliente` | `person.name` |
| `#CPF` | `person.identifier` |
| `#ENDEREÇO`, `#CEP`, `#CIDADE`, `#uf`, `#bai`, `#nun` | `person.address.*` |
| `#LATITUDE`/`#LONGITUDE` | `person.address.latitude/longitude` (nem sempre preenchido) |
| `#cel`/`#tel` | `person.phone` |
| `#VALOR PROJETO` | `deal.value` |
| `#VALOR KIT` | custom field "Valor do KIT" do deal |
| `#POT kWp` | custom field "Potência em kWp" do deal (ou `proposals.fullPower`) |
| `#VALOR CONTA` | `indicacoes.conta_energia_estimada` local (quando veio de indicação) |
| `#FORMAPAGAMENTO` | custom field "Forma de Pagamento:" do deal |
| Medições (DWG) | custom field "Medições:" do deal |
| `#DATA`, códigos `PJ-/CT-/MD-/DE-`, valores por extenso | calculados pelo servidor |
| `#resptecnico`, `#reg`, `#projetista` | constantes da Tecsol (config) |

### SEM fonte exposta na API hoje (validar com o dono / devs da Solarz)
| Variável | Onde vive hoje |
|---|---|
| `#FAB MOD`, `#MOD MOD`, `#POT MOD`, `#QTD MOD`, `#AREA` | proposta na Solarz (equipamentos da Fortlev) — a Open API não expõe |
| `#TIPO INV`, `#FAB INV`, `#MOD INV`, `#N° MPPT`, `#POT INV`, `#QTD INV`, distribuição MPPT | idem |
| `#GERACAO` (kWh/mês) | proposta ("Geração esperada") — pergunta já enviada aos devs |
| `#N° INSTALAÇÃO` (UC), `#GRUPO`, `#CLASSE`, `#TIPO DE CONEXAO`, `#DISJUNTOR`, `#TENSAO`, cabos | não achado em nenhum campo da API |
| `#N° TRT CFT` | digitado no form do card (engenheiro gera no site do governo) |
| `numero_pedido` | campo no form do card, pré-preenchido com o próximo da sequência (01, 02, ...) |

> Decisão pendente: pros campos "sem fonte", (a) a Tecsol cria campos custom
> no deal da Solarz com esses nomes (a API expõe custom fields do deal, nós
> lemos automaticamente), ou (b) ficam como campos digitáveis na tela de
> geração junto de pedido/CFT. Precisa da palavra do dono.

## Perguntas em aberto (validar com o dono)
1. DWG será gerado por máquina Windows com AutoCAD (macros usam COM,
   `AcadDoc`/`AlterarTextos`) — qual máquina cumpre esse papel?
2. Campos de cabos/disjuntor: regra de cálculo ou preenchimento na Solarz?
3. Opção (a) ou (b) da decisão pendente acima?
