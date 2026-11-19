# GRAFOS_UNIFEI

Lê os currículos Lattes (HTML) dos docentes da UNIFEI e gera os 4 datasets da rede de
colaboração acadêmica, com o IMC como camada central. Cada relação liga um professor do IMC a
outra pessoa e guarda, em 5 dimensões, os códigos das atividades que os dois fizeram juntos.

## As cinco dimensões (nesta ordem em todos os vetores)

ART (artigos e trabalhos completos em anais) · PRJ (projetos de pesquisa) · ORI (orientações
concluídas) · BAN (bancas) · PTT (produção técnico-tecnológica).

## Os 4 CSVs (`backend/data/raw/`)

UTF-8 com BOM, fim de linha `\r\n`, listas gravadas como JSON. Números da execução com
`Professores_v7_somente_HTML.zip` (521 currículos, 93.970 registros, 81.942 atividades únicas):

| Arquivo | Uma linha por | Linhas |
|---|---|---|
| `dataset_completo_UNIFEI.csv` | docente (id, nome, instituto, área, SIAPE, link Lattes) | 549 |
| `dataset_entrada_IMC.csv` | pesquisador da rede, com os códigos das suas atividades | 1.534 |
| `dataset_saida_IMC.csv` | relação (par de pesquisadores) com vetor bruto e vetor contagem | 3.256 |
| `dataset_atividades_IMC.csv` | atividade única (título, ano, participantes, fontes...) | 56.709 |

Os códigos dos vetores (ex.: `ART-001804`) são o `id_atividade` do dataset de atividades.
O `pesquisador_id` é o SIAPE; sem SIAPE, `PROV-L<Lattes>` ou `PROV-N<hash>`. Externos recebem
`EXT-L<Lattes>` (vistos com link) ou `EXT-N<hash do nome>`.

## Requisitos

Python 3.9 ou mais novo, `beautifulsoup4` e `lxml`. Já estão no `requirements.txt` do backend; a mineração usa o mesmo `.venv` do backend.

## Como rodar

Coloque o ZIP em `mineracao/dados/brutos/Professores_v8.zip` (ou passe outro com `--entrada`).
Na primeira execução ele é extraído em `dados/temporarios/`; se a extração for interrompida,
apague essa pasta e rode de novo. A execução leva cerca de 70 segundos.

De dentro de `backend/`, com o `.venv` do backend ativado:

```bash
python mineracao/main.py
```

Os CSVs são gravados em `backend/data/raw/`, onde a API os lê. Rode a mineração antes de subir o backend.

Opções: `--entrada` (ZIP ou pasta já extraída) e `--saida` (pasta dos CSVs, padrão
`backend/data/raw`). Exemplo: `python mineracao/main.py --entrada outro.zip --saida /tmp/teste`.

## Estrutura esperada do ZIP

```text
IMC - Instituto de Matemática e Computação/
├── IMC.txt                      índice: nome - link Lattes - link SIGAA (siape=...)
└── Nome do Professor/
    └── Currículo do Sistema de Currículos Lattes (Nome do Professor).html
IFQ - Instituto de Física e Química/
└── ...
```

A primeira palavra do nome da pasta do instituto precisa estar em `SIGLA_POR_PASTA`
(`configuracao.py`).

## As 6 etapas (`main.py`)

1. `professores.py` + `indices.py`: lê os índices `.txt`, as pastas e o cabeçalho de cada CV;
   cada professor ganha um id (SIAPE).
2. `curriculos.py` + `dimensoes.py`: percorre o HTML e extrai os itens das 5 dimensões.
3. `identificacao.py` + `externos.py`: descobre quem é cada nome (níveis 1 a 5) e corrige
   externos que na verdade são professores.
4. `deduplicacao.py` + `evidencias.py` + `consolidacao.py`: junta o mesmo artigo registrado no CV
   de cada coautor numa atividade única (union-find).
5. `rede.py`: monta os pares, numera as atividades e calcula os vetores.
6. `csvs.py`: grava os 4 CSVs.

Constantes (caminhos, siglas, seções do Lattes, limiares) ficam em `configuracao.py`;
funções de texto usadas por várias etapas, em `src/textos.py`.

## Correspondências confirmadas à mão

`correspondencias_confirmadas.json` guarda identidades revisadas por uma pessoa: formas de
citação (`citacoes`) e Lattes iDs (`lattes`) que pertencem a um professor. O sistema nunca une
abreviações ou nomes parecidos sozinho; só usa o que estiver nesse arquivo. Sem ele, os CSVs mudam.

## Limitações essenciais

- Coautores citados só por abreviação (`MELO, D. S.`), sem link Lattes, não são identificados e
  ficam fora da rede (vão para `nomes_nao_resolvidos`). É de propósito: evita relações falsas.
- 28 docentes não têm currículo no ZIP; só aparecem quando outro currículo os cita, e suas
  colunas de atividades ficam vazias (nunca zero). Externos também não têm área nem atividades.
- O extrator depende das classes do HTML do Lattes (`title-wrapper`, `inst_back`,
  `cita-artigos`, `layout-cell-11`); se o CNPq mudar o layout, `src/curriculos.py` precisa de ajuste.
- Título e ano de bancas, orientações e produção técnica saem de regras de texto: o Lattes não
  separa esses campos.
- Cada currículo é interpretado duas vezes (cabeçalho na etapa 1, itens na etapa 2): guardar as
  521 páginas já interpretadas custaria cerca de 2 GB de memória.

## Dados pessoais

Os currículos e os CSVs têm nome, SIAPE e link do Lattes dos docentes. A pasta `dados/` não vai
para o repositório (`.gitignore`); trate os CSVs com o mesmo cuidado.
