# Mineração dos currículos Lattes

Lê os currículos Lattes (HTML) dos docentes da UNIFEI e gera os **4 CSVs** que alimentam o backend da
Rede de Colaboração IMC. Cada relação liga um pesquisador do IMC a outra pessoa e guarda, em cinco
dimensões, as atividades que os dois fizeram juntos.

> Visão geral do projeto (backend e frontend): [README do rede-imc](../../README.md).

---

## Em resumo

```
dados/brutos/Professores_v8.zip  ──►  python mineracao/main.py  ──►  backend/data/raw/*.csv
        (521 currículos)                  6 etapas, ~70 s              (lidos pela API)
```

Última execução, com `Professores_v8.zip`:

| | |
|---|---|
| Currículos lidos | 521 |
| Registros extraídos | 97.223 |
| Atividades únicas (após juntar repetições) | 83.671 |
| Relações na rede do IMC | 2.990 |

---

## Como rodar

A mineração usa o mesmo ambiente Python do backend. Se o `.venv` ainda não existe, veja o
[README do rede-imc](../../README.md#1-preparar-o-ambiente-python-só-na-primeira-vez).

De dentro de `backend/`, com o `.venv` ativo:

```bash
python mineracao/main.py
```

A saída mostra o andamento:

```
[1/6] Lendo índices, pastas e cabeçalhos dos currículos...
[2/6] Extraindo as cinco dimensões de cada currículo...
[3/6] Conferindo externos que podem ser professores ou que têm dois ids...
   1551 externos citados só pelo nome passaram a usar o id do Lattes
   aviso: ... (nomes de dois Lattes e Lattes suspeitos, para revisão)
   115 externos com o nome do meio faltando foram juntados ao nome completo
   aviso: ... (nome que cabe em dois nomes e dois Lattes com nomes parecidos)
[4/6] Juntando registros repetidos em atividades únicas...
[5/6] Montando os pares e os vetores da camada...
[6/6] Gravando os 4 CSVs...
Pronto: 97223 registros, 83671 atividades únicas, 2990 relações. CSVs em .../backend/data/raw
```

### Opções

| Opção | Padrão | Uso |
|---|---|---|
| `--entrada` | `mineracao/dados/brutos/Professores_v8.zip` | Outro ZIP ou uma pasta já extraída |
| `--saida` | `backend/data/raw` | Outra pasta para os CSVs |

```bash
python mineracao/main.py --entrada outro.zip --saida /tmp/teste
```

Na primeira execução, o ZIP é extraído em `mineracao/dados/temporarios/`. Se a extração for
interrompida, apague essa pasta e rode de novo.

---

## Entrada: o ZIP dos currículos

Uma pasta por instituto, com um índice `.txt` e uma pasta por professor:

```
IMC - Instituto de Matemática e Computação/
├── IMC.txt              nome - link Lattes - link SIGAA (siape=...)
└── Nome do Professor/
    └── Currículo do Sistema de Currículos Lattes (Nome do Professor).html
IFQ - Instituto de Física e Química/
└── ...
```

A primeira palavra do nome da pasta (`IMC`, `IFQ`, `UA1`...) precisa estar em `SIGLA_POR_PASTA`,
no `configuracao.py`. É ali que `UA1` vira `ICT`, por exemplo.

---

## Saída: os 4 CSVs

Gravados em `backend/data/raw/`, em UTF-8 com BOM (abre com acentos no Excel), fim de linha `\r\n`
e listas no formato JSON. **O backend depende desses nomes e colunas.**

| Arquivo | Uma linha por | Linhas |
|---|---|---|
| `dataset_completo_UNIFEI.csv` | docente da UNIFEI | 549 |
| `dataset_entrada_IMC.csv` | pesquisador da rede do IMC | 1.311 |
| `dataset_saida_IMC.csv` | relação (dupla de pesquisadores) | 2.990 |
| `dataset_atividades_IMC.csv` | atividade única | 57.609 |

**`dataset_completo_UNIFEI.csv`**: cadastro dos docentes: `pesquisador_id`, `nome`, `instituto`, `area`, `ciape`, `lattes_url`.

**`dataset_entrada_IMC.csv`**: os vértices da rede. Para cada pesquisador: nome, instituto, área,
uma coluna por dimensão com os códigos das atividades (ex.: `["ART-002164", ...]`) e o
`vetor contagem` (`[ART, PRJ, ORI, BAN, PTT]`).

**`dataset_saida_IMC.csv`**: as arestas. Os dois pesquisadores, seus institutos e áreas, o
`tipo de relacao` (`IMC-IMC`, `IMC-IFQ`, `IMC-EXT`...), o `vetor bruto` (códigos das atividades em
comum por dimensão) e o `vetor contagem`.

**`dataset_atividades_IMC.csv`**: o que cada código significa: dimensão, tipo, título, ano, DOI,
participantes, de qual currículo veio e como cada pessoa foi identificada.

### Identificadores

| Formato | Quem é |
|---|---|
| `1234567` | Docente da UNIFEI, pelo SIAPE |
| `PROV-L<lattes>` / `PROV-N<hash>` | Docente sem SIAPE (pelo Lattes ou pelo nome) |
| `EXT-L<lattes>` | Externo identificado por link do Lattes |
| `EXT-N<hash>` | Externo identificado pelo nome completo |

Os códigos de atividade (`ART-000001`, `PRJ-000001`...) são o `id_atividade` do dataset de atividades.

---

## As 6 etapas

| # | Etapa | Módulos em `src/` |
|---|---|---|
| 1 | Lê os índices `.txt`, as pastas e o cabeçalho de cada currículo. Cada professor ganha um id (SIAPE) | `professores.py`, `indices.py` |
| 2 | Percorre o HTML e extrai os itens das 5 dimensões | `curriculos.py`, `dimensoes.py` |
| 3 | Descobre quem é cada nome citado, corrige externos que na verdade são professores e junta o externo que ganhou dois ids | `identificacao.py`, `externos.py` |
| 4 | Junta o mesmo item registrado no currículo de cada coautor em uma atividade única | `deduplicacao.py`, `evidencias.py`, `consolidacao.py` |
| 5 | Monta as duplas (só com o que conta como colaboração), numera as atividades e calcula os vetores | `rede.py` |
| 6 | Grava os 4 CSVs | `csvs.py` |

Funções de texto usadas por várias etapas ficam em `src/textos.py`. Todas as constantes (caminhos,
siglas, seções do Lattes e limiares de semelhança) ficam em `configuracao.py`. Para mudar uma regra,
mude lá.

### Como um nome é identificado (etapa 3)

Do mais confiável para o menos confiável:

1. O próprio item traz o link do Lattes da pessoa.
2. É o dono do currículo (nome em negrito ou forma de citação declarada).
3. Nome completo igual ao de um docente.
4. Forma de citação que pertence a um único docente.
5. Nome completo de alguém de fora da UNIFEI, que vira um externo (`EXT-N`).

Nomes que não passam em nenhum nível (como `MELO, D. S.` sem link) **ficam fora da rede**, de
propósito, para não criar relações falsas. Eles aparecem na coluna `nomes_nao_resolvidos`.

Texto com palavra de instituição (`UNIVERSIDADE`, `INSTITUTO`, `FACULDADE`… lista
`PALAVRAS_DE_INSTITUICAO` no `configuracao.py`) não é pessoa: endereços e afiliações lidos como
autor são descartados e não entram nem em `nomes_nao_resolvidos`.

**Externo com dois ids.** A mesma pessoa pode virar `EXT-L` num currículo (com link) e `EXT-N` em
outro (só o nome). No fim da etapa 3, o `EXT-N` passa a usar o id do `EXT-L` quando o seu nome
completo (sem acento, maiúsculas/minúsculas, espaços e partículas como "de" e "da" ignorados)
pertence a um único `EXT-L`. Essa é a única junção de externos por nome: as etapas seguintes não
trocam ids.
Não juntam, e aparecem como `aviso:` na saída para revisão:

- nome que pertence a dois `EXT-L` diferentes (podem ser pessoas diferentes);
- `EXT-L` suspeito: dois nomes completos dele sem nenhuma palavra em comum (link do Lattes errado
  no currículo, repetido em vários coautores). Esse Lattes fica fora da comparação.

Nome abreviado nunca junta.

**Externo com o nome do meio faltando.** Depois disso, dois externos viram a mesma pessoa quando
têm o mesmo primeiro e último nome, todas as palavras do nome mais curto estão no mais longo
(`Jorge Sotomayor Tello` e `Jorge Manuel Sotomayor Tello`), nenhum dos dois está abreviado e eles
têm pelo menos um coautor em comum (`COAUTORES_EM_COMUM_PARA_JUNTAR`), sem nunca aparecerem juntos
no mesmo item. Fica o id do Lattes, quando houver. Não juntam, e viram `aviso:`, o nome curto que
cabe em dois nomes longos e dois `EXT-L` (dois Lattes são duas pessoas).

**Banca registrada por vários membros (etapa 4).** Cada membro registra a mesma banca no próprio
currículo, às vezes com o nome do aluno escrito de outro jeito. Viram uma banca só quando têm o
mesmo candidato (sem partículas, `Jr` = `Junior`), ano e tipo; ou, com o nome do aluno diferente
(`Rezende` e `Resende`), o mesmo ano e tipo, nomes com pelo menos 2 palavras em comum
(`PALAVRAS_EM_COMUM_DO_CANDIDATO`), o dono de um registro identificado no outro e título com
semelhança de pelo menos 0,8 (`SIMILARIDADE_BANCA_CANDIDATO_DIFERENTE`).

**Ano.** Vale o ano no padrão do Lattes, entre pontos logo depois do título (`Título. 2016.`),
quando ele difere do primeiro ano encontrado no texto (`Portaria no. 2074` não é ano).

## O que conta como colaboração

Uma dupla só soma uma atividade quando os dois colaboraram nela (`colaboracao_valida`, em
`rede.py`). Os papéis ficam em `configuracao.py`.

| Dimensão | Conta | Não conta |
|---|---|---|
| Orientação | os dois supervisionaram juntos (orientador, coorientador, orientador não especificado) | orientador com o aluno (`orientando`) |
| Banca | os dois eram membros | qualquer pessoa com papel que contenha `candidato` (inclusive `candidato/membro`) |
| Artigo, projeto, produção técnica | todos os participantes | — |

Alguns currículos escrevem o próprio aluno na lista de membros da banca (`...; FRANCISCO, C. S. L.
Participação em banca de Christopher de Souza Lima Francisco`). Esse nome entra como `candidato`
quando é igual ao do aluno ou quando é uma citação específica com o último sobrenome e as
iniciais do aluno (`eh_o_candidato`, em `dimensoes.py`). Citação genérica (`SILVA, B`) e o dono
do currículo nunca viram candidato.

Por isso nenhuma relação sai com o vetor todo zero, e quem só aparecia como aluno (orientando ou
candidato) fica fora da rede. Os docentes do IMC continuam todos no `dataset_entrada`, mesmo sem
relação (com a observação "sem relação identificada").

---

## Correspondências confirmadas à mão

`correspondencias_confirmadas.json` guarda identidades revisadas por uma pessoa:

- `citacoes`: formas de citação (`SOBRENOME, I. N.`) que pertencem a um docente;
- `lattes`: links do Lattes que pertencem a docentes sem Lattes no cadastro.

A mineração **nunca** junta abreviações ou nomes parecidos sozinha; só usa o que estiver nesse
arquivo. Mudar o arquivo muda os CSVs.

---

## Limitações

- **Coautores só abreviados** e sem link do Lattes não são identificados (ver etapa 3).
- **28 docentes não têm currículo no ZIP.** Eles só aparecem quando outro currículo os cita, e suas
  colunas de atividades ficam vazias (não zero). Externos também não têm área nem atividades próprias.
- **Depende do layout do Lattes.** O extrator usa classes do HTML (`title-wrapper`, `inst_back`,
  `cita-artigos`, `layout-cell-11`). Se o CNPq mudar a página, `src/curriculos.py` precisa de ajuste.
- **Título e ano** de bancas, orientações e produção técnica saem de regras de texto, porque o Lattes
  não separa esses campos.
- Só entram **orientações concluídas**. As em andamento ficam de fora.

