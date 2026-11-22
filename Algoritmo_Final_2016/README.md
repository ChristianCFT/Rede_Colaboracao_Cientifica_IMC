# Rede de colaboração do IMC (UNIFEI)

Análise da colaboração entre docentes do IMC, com algoritmos de grafos (projeto SMAC03).

## Como rodar

1. Instale o Python 3.11 ou mais recente e as bibliotecas:
   `python -m pip install pandas numpy networkx scikit-learn openpyxl`
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

## Pendências

- Resolvidas com a troca para os CSVs da mineração: a base agora é a própria saída da mineração (só relações com docente do IMC, regra de papéis aplicada); as 340 linhas com chave repetida eram atividades diferentes com título genérico; o artigo de 2027 saiu.
- Na mineração: o projeto RMMAT-MG ainda aparece duas vezes (PRJ-001746 e PRJ-001750), e há outras duplicatas pequenas (mesmo DOI, mesmo registro de software, mesma banca com nome de aluno escrito diferente). O RMMAT-MG pesa muito: está em 105 das 262 relações entre docentes do IMC (40%); sem ele a Matemática cai de 108 para 76 relações e o maior clique da área de 13 para 6 docentes. Isso infla o ranking por número de ligações do Q1.
- Quatro docentes do IMC estão sem área no cadastro (aparecem como "Sem área" no Q1 e "OUTRA" nas camadas); um deles também não tem nenhuma atividade no período, por isso o Q2 mostra 48 docentes e as demais análises 49.
- Q1, Q2 e camadas classificam a área do mesmo jeito (Computação ou Matemática em qualquer área do cadastro: 16 e 25 docentes).

## Sigilo

Os dados são de docentes e pesquisadores. Não publique os CSVs nem as bases.
