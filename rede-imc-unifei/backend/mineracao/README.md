# Mineração dos currículos Lattes

Lê os currículos Lattes (HTML) dos docentes da UNIFEI e gera os **4 CSVs** que alimentam o backend da
Rede de Colaboração IMC. Cada relação liga um pesquisador do IMC a outra pessoa e guarda, em cinco
dimensões, as atividades que os dois fizeram juntos.

> Visão geral do projeto (backend e frontend): [README do rede-imc](../../README.md).

```
dados/brutos/Professores_v8.zip  ──►  python mineracao/main.py  ──►  backend/data/raw/*.csv
        (currículos Lattes)               6 etapas, ~70 s              (lidos pela API)
```

---

## Como rodar

A mineração usa o mesmo ambiente Python do backend. Se o `.venv` ainda não existe, veja o
[README do rede-imc](../../README.md#1-preparar-o-ambiente-python-só-na-primeira-vez).

De dentro de `backend/`, com o `.venv` ativo:

```bash
python mineracao/main.py
```

A saída mostra o andamento de cada etapa e termina com o resumo:

```
[1/6] Lendo índices, pastas e cabeçalhos dos currículos...
[2/6] Extraindo as cinco dimensões de cada currículo...
[3/6] Conferindo externos que podem ser professores ou que têm dois ids...
   1551 externos citados só pelo nome passaram a usar o id do Lattes
   115 externos com o nome do meio faltando foram juntados ao nome completo
[4/6] Juntando registros repetidos em atividades únicas...
[5/6] Montando os pares e os vetores da camada...
[6/6] Gravando os 4 CSVs...
Pronto: 97223 registros, 83671 atividades únicas, 2990 relações. CSVs em .../backend/data/raw
```

| Opção | Padrão | Uso |
|---|---|---|
| `--entrada` | `mineracao/dados/brutos/Professores_v8.zip` | Outro ZIP ou uma pasta já extraída |
| `--saida` | `backend/data/raw` | Outra pasta para os CSVs |

```bash
python mineracao/main.py --entrada outro.zip --saida /tmp/teste
```

Na primeira execução, o ZIP é extraído em `mineracao/dados/temporarios/`.

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

A primeira palavra do nome da pasta (`IMC`, `IFQ`, `UA1`...) precisa estar em `SIGLA_POR_PASTA`, no
`configuracao.py`. É ali que `UA1` vira `ICT`, por exemplo.

---

## Saída: os 4 CSVs

Gravados em UTF-8 com BOM (abre com acentos no Excel), com listas no formato JSON. O backend depende
desses nomes e colunas.

| Arquivo | Uma linha por | Linhas |
|---|---|---|
| `dataset_completo_UNIFEI.csv` | docente da UNIFEI | 549 |
| `dataset_entrada_IMC.csv` | pesquisador da rede do IMC (vértice) | 1.311 |
| `dataset_saida_IMC.csv` | relação entre um pesquisador do IMC e outro (aresta) | 2.990 |
| `dataset_atividades_IMC.csv` | atividade única | 57.609 |

- **`dataset_completo_UNIFEI`**: `pesquisador_id`, `nome`, `instituto`, `area`, `ciape`, `lattes_url`.
- **`dataset_entrada_IMC`**: nome, instituto, área, uma coluna por dimensão com os códigos das atividades
  (ex.: `["ART-002164", ...]`), `pesquisador_id`, `vetor contagem` e `observacao`.
- **`dataset_saida_IMC`**: os dois pesquisadores, seus institutos e áreas, o `tipo de relacao`
  (`IMC-IMC`, `IMC-IFQ`, `IMC-EXT`...), o `vetor bruto` (códigos por dimensão) e o `vetor contagem`.
  As relações entre dois docentes do IMC aparecem uma vez do ponto de vista de cada um.
- **`dataset_atividades_IMC`**: o que cada código significa: dimensão, tipo, título, ano, DOI,
  participantes, papéis, de qual currículo veio e como cada pessoa foi identificada.

O vetor segue sempre a ordem `[ART, PRJ, ORI, BAN, PTT]`.

| Identificador | Quem é |
|---|---|
| `1234567` | Docente da UNIFEI, pelo SIAPE |
| `PROV-L<lattes>` / `PROV-N<hash>` | Docente sem SIAPE (pelo Lattes ou pelo nome) |
| `EXT-L<lattes>` | Externo identificado pelo link do Lattes |
| `EXT-N<hash>` | Externo identificado pelo nome completo |

---

## A lógica: as 6 etapas

| # | Etapa | Módulos em `src/` |
|---|---|---|
| 1 | Lê os índices `.txt`, as pastas e o cabeçalho de cada currículo. Cada professor ganha um id | `professores.py`, `indices.py` |
| 2 | Percorre o HTML e extrai os itens das 5 dimensões: título, ano e participantes | `curriculos.py`, `dimensoes.py` |
| 3 | Descobre quem é cada nome citado e junta os registros da mesma pessoa externa | `identificacao.py`, `externos.py` |
| 4 | Junta o mesmo item registrado no currículo de cada coautor numa atividade única | `deduplicacao.py`, `evidencias.py`, `consolidacao.py` |
| 5 | Monta as duplas (só com o que conta como colaboração), numera as atividades e calcula os vetores | `rede.py` |
| 6 | Grava os 4 CSVs | `csvs.py` |

### Como um nome é identificado (etapa 3)

Do mais confiável para o menos confiável:

1. O próprio item traz o link do Lattes da pessoa.
2. É o dono do currículo (nome em negrito ou forma de citação declarada).
3. Nome completo igual ao de um docente.
4. Forma de citação que pertence a um único docente.
5. Nome completo de alguém de fora da UNIFEI, que vira um externo (`EXT-N`).

Nomes que não passam em nenhum nível ficam na coluna `nomes_nao_resolvidos`, fora da rede. Depois da
leitura, o mesmo externo citado de formas diferentes (com link do Lattes num currículo e só pelo nome em
outro, ou com o nome do meio faltando) vira um único pesquisador.

### O que conta como colaboração (etapa 5)

| Dimensão | Conta |
|---|---|
| Artigo, projeto, produção técnica | todos os participantes identificados |
| Orientação | os dois orientaram juntos (orientador e coorientador) |
| Banca | os dois avaliaram juntos (o candidato não conta) |

---

## Estrutura do código

```
mineracao/
├── main.py                          roda as 6 etapas em ordem
├── configuracao.py                  constantes: caminhos, siglas, seções do Lattes, papéis e limiares
├── correspondencias_confirmadas.json  formas de citação e Lattes confirmados à mão
├── dados/brutos/Professores_v8.zip  entrada
└── src/
    ├── textos.py                    normalização de textos e nomes (usada por todas as etapas)
    ├── indices.py, professores.py   etapa 1
    ├── curriculos.py, dimensoes.py  etapa 2
    ├── identificacao.py, externos.py  etapa 3
    ├── deduplicacao.py, evidencias.py, consolidacao.py  etapa 4
    ├── rede.py                      etapa 5
    └── csvs.py                      etapa 6
```

Cada regra fica numa função pequena, e as constantes ficam no `configuracao.py`: para mudar uma regra
(papéis, limiares de semelhança, siglas), mude lá. O arquivo `correspondencias_confirmadas.json` guarda
identidades revisadas por uma pessoa; mudar esse arquivo muda os CSVs.
