# Modelos dos documentos gerados

Coloque aqui os `.docx` que a engenharia já usa, com estes nomes:

| Arquivo | Documento |
|---|---|
| `memorial.docx` | Memorial Descritivo |
| `contrato.docx` | Contrato |
| `procuracao.docx` | Procuração |
| `rt.docx` | Registro de Responsabilidade Técnica |

Dentro do documento, escreva as variáveis **exatamente** como na planilha
`CONTROLE PROJETOS ENGENHARIA.xlsm` (abas LINHA BASE e ART) — o gerador troca
cada uma pelo valor do projeto:

`#NOME PF`, `#CPF`, `#ENDEREÇO`, `#CEP`, `#CIDADE`, `#uf`, `#tel`, `#uc`,
`#DATA`, `#N° PROJETO`, `#N° CONTRATO`, `#MEMORIAL`, `#N° TRT CFT`, `#PEDIDO`,
`#POT kWp`, `#GERACAO`, `#VALOR PROJETO`, `#VALORPROJETOEXT`, `#VALOR KIT`,
`#VALORKITEXT`, `#FORMAPAGAMENTO`, `#resptecnico`, `#reg`,
`#FAB MOD`, `#MOD MOD`, `#POT MOD`, `#QTD MOD`, `#FAB INV`, `#MOD INV`, ...

A lista completa está em `app/documentos_gerador.py` (`montar_variaveis`).

Funciona em parágrafos, tabelas, cabeçalho e rodapé. Documento sem modelo é
apenas pulado — os outros continuam sendo gerados.

**Atenção:** as variáveis de equipamento (`#FAB MOD`, `#MOD INV`, ...) e a
`#GERACAO` ainda ficam vazias, porque a API da Solarz não expõe esses campos
hoje (ver `contracts/campos_faltantes_solarz.json`).
