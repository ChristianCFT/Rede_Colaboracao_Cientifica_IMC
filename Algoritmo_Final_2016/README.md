# Rede de colaboração do IMC (UNIFEI)

Análise da colaboração entre docentes do IMC, com algoritmos de grafos (projeto SMAC03).

## Como rodar

1. Instale o Python 3.11 ou mais recente e as bibliotecas listadas no `requirements.txt`:
   `python -m pip install -r requirements.txt`
2. Coloque na pasta os 4 CSVs da mineração (já com o recorte 2016–2026).
3. Rode `menu_imc.py` e escolha uma opção:
   - **1:** monta a base 2016–2026 a partir dos CSVs da mineração (alguns segundos)
   - **2:** Questão 1 (grupos, trios e influência)
   - **3:** Questão 2 (elos com a UNIFEI e remoção)
   - **4:** análise das quatro camadas
   - **5:** roda 1, 2, 3 e 4 em sequência
   - **6:** verifica os arquivos da pasta

Sempre que trocar os CSVs, rode a opção 1 (ou a 5) de novo.

## Arquivos

**Código**
- `requirements.txt`: dependências Python (pandas, numpy, networkx, scikit-learn, openpyxl).
- `menu_imc.py`: menu de execução.
- `montar_base.py`: gera a base 2016–2026 a partir dos CSVs da mineração (usado pelas opções 1 e 5).
- `build_base_v4.py`: versão antiga, que reconstruía a base a partir das atividades; fica na pasta, mas o menu não o usa mais.
- `q1_terminal.py`, `q2_elos.py`, `analise_camadas.py`: as análises.
- `grafos_smac03.py`: biblioteca de algoritmos (não roda sozinha).

**Dados**
- `dataset_entrada_IMC.csv` e `dataset_saida_IMC.csv`: entrada da opção 1 (pessoas e relações da rede do IMC).
- `dataset_atividades_IMC.csv`: só para a opção 1 conferir se os anos estão entre 2016 e 2026.
- `dataset_IMC_2016_2026.xlsx`: base usada pelas opções 2, 3 e 4 (abas `entrada` e `saida`).
- `dataset_completo_UNIFEI.csv`: cadastro com área, usado na opção 4.
- `dataset_IMC_v4.xlsx`: referência da versão antiga; os scripts não o usam.

## Saídas

Cada análise imprime no terminal. Para salvar em arquivo:
`python q1_terminal.py > Q1_saida.txt`


