# Rede de colaboração do IMC (UNIFEI)

Análise da colaboração entre docentes do IMC, com algoritmos de grafos (projeto SMAC03).

## Como rodar

1. Instale o Python 3.11 ou mais recente e as bibliotecas:
   `python -m pip install pandas numpy networkx scikit-learn openpyxl`
2. Rode `menu_imc.py` e escolha uma opção:
   - **1:** reconstrói a base 2016–2026 (cerca de 1 minuto)
   - **2:** Questão 1 (grupos, trios e influência)
   - **3:** Questão 2 (elos com a UNIFEI e remoção)
   - **4:** análise das quatro camadas
   - **5:** roda 1, 2, 3 e 4 em sequência
   - **6:** verifica os arquivos da pasta

Se já tiver `dataset_IMC_2016_2026.xlsx`, pode pular a opção 1.

## Arquivos

**Código**
- `menu_imc.py`: menu de execução.
- `build_base_v4.py`: gera a base 2016–2026 a partir das atividades.
- `q1_terminal.py`, `q2_elos.py`, `analise_camadas.py`: as análises.
- `grafos_smac03.py`: biblioteca de algoritmos (não roda sozinha).

**Dados**
- `dataset_atividades_IMC.csv` e `dataset_entrada_IMC.csv`: entrada da opção 1.
- `dataset_IMC_2016_2026.xlsx`: base usada pelas opções 2, 3 e 4.
- `dataset_completo_UNIFEI.csv`: cadastro com área, usado na opção 4.
- `dataset_IMC_v4.xlsx` e `dataset_saida_IMC.csv`: referência; os scripts não os usam.

## Saídas

Cada análise imprime no terminal. Para salvar em arquivo:
`python q1_terminal.py > Q1_saida.txt`

## Pendências

- A base oficial ainda não está confirmada: a projeção das atividades não reproduz `dataset_saida_IMC.csv`.
- Há 340 linhas com chave repetida, contadas duas vezes.
- Há uma atividade com ano 2027.

## Sigilo

Os dados são de docentes e pesquisadores. Não publique os CSVs nem as bases.
