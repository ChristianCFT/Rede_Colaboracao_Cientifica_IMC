# Rede de Colaboração Científica do IMC/UNIFEI

Projeto da disciplina SMAC03 – Grafos (UNIFEI, 2º semestre de 2026), Cenário 4: Mapa do Conhecimento da
Colaboração Científica da UNIFEI.

A partir dos currículos Lattes e do SIGAA, o projeto monta a rede de colaboração dos docentes do Instituto de
Matemática e Computação (IMC) de 2016 a 2026 e a analisa com algoritmos de grafos. A colaboração não se
limita à coautoria: cada ligação reúne artigos, projetos, orientações, bancas e produção técnica.

## Modelo

- **Vértices:** pesquisadores (docentes do IMC, docentes de outros institutos da UNIFEI e pesquisadores externos).
- **Arestas:** colaboração entre dois pesquisadores, com a contagem de atividades em comum em cada uma das cinco dimensões.
- **Peso:** `W = Σ α · ln(1 + x) / ln(1 + M)`, entre 0 e 1, em que `x` é a contagem da dimensão e `M` o maior valor dela na rede.
  α: artigos 0,40, projetos 0,20, orientações 0,20, produção técnica 0,15 e bancas 0,05.
- **Camadas de análise:** (1) Computação do IMC, (2) todo o IMC, (3) IMC e outros institutos da UNIFEI, (4) rede completa, com os externos.

Algoritmos usados: BFS, Tarjan (pontos de articulação e pontes), Kruskal (árvore geradora máxima),
Dijkstra/Brandes (intermediação) e Louvain (comunidades).

## Principais resultados

- A rede tem 817 pesquisadores e 1.710 relações. Integrar as cinco dimensões revela 3,3 vezes mais relações que a coautoria sozinha.
- Computação e Matemática funcionam como duas redes separadas dentro do IMC: há só dois vínculos entre as áreas.
- O peso reduz a influência das bancas (de 47,1% das atividades para 8,9% do peso) e muda quem aparece como ponte.

## Organização

| Pasta | Branch | Conteúdo |
|---|---|---|
| [`dados_saida/`](https://github.com/ChristianCFT/Rede_Colaboracao_Cientifica_IMC/tree/main/dados_saida) | `main` | Os 4 CSVs gerados pela mineração e a documentação das colunas |
| [`rede-imc/`](https://github.com/ChristianCFT/Rede_Colaboracao_Cientifica_IMC/tree/feature/interface/rede-imc) | `feature/interface` | Mineração dos currículos, API (FastAPI) e interface web (TypeScript) |
| [`recorte_2016/`](https://github.com/ChristianCFT/Rede_Colaboracao_Cientifica_IMC/tree/feature/interface/recorte_2016) | `feature/interface` | Recorte dos CSVs para as atividades de 2016 a 2026 |
| [`Algoritmo_Final_2016/`](https://github.com/ChristianCFT/Rede_Colaboracao_Cientifica_IMC/tree/feature/algoritmo/Algoritmo_Final_2016) | `feature/algoritmo` | Análises: grupos (Q1), elos e simulação de remoção (Q2) e as quatro camadas |
| [`rede-imc/analise/`](https://github.com/ChristianCFT/Rede_Colaboracao_Cientifica_IMC/tree/feature/analise-grafos/rede-imc/analise) | `feature/analise-grafos` | Análise complementar da rede do IMC |
| [`docs/`](docs/) | `main` | Relatório (PDF e fonte em LaTeX) e slides da apresentação |

Cada pasta tem um README com os detalhes.

## Como executar

Requisitos: Python 3.11 ou mais recente e Node.js 18 ou mais recente.

**Interface** (branch `feature/interface`)

```bash
cd rede-imc/backend
python -m venv .venv
source .venv/bin/activate          # Windows (PowerShell): .venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn src.main:app --port 8000
```

Em outro terminal:

```bash
cd rede-imc/frontend
npm install
npm run dev
```

Depois, abra <http://localhost:5173>. A mineração (`python mineracao/main.py`, dentro de `backend/`) só
precisa rodar de novo se os currículos mudarem.

**Análises** (branch `feature/algoritmo`)

```bash
cd Algoritmo_Final_2016
pip install pandas numpy networkx scikit-learn openpyxl
python menu_imc.py
```

No menu, a opção 1 monta a base de 2016 a 2026 e a opção 5 roda todas as análises em sequência.

## Equipe

| Integrante | Papel |
|---|---|
| Christian Ferreira Toledo | Coordenador |
| Mateus Eduardo de Padua Almeida | Modelador |
| Thiago Santos Fonseca Amaral | Modelador |
| João Pedro de Andrade Santos | Desenvolvedor |
| Leonardo Coura de Oliveira | Desenvolvedor |

Professor: Rafael Frinhani

## Licença

MIT. Veja o arquivo [LICENSE](LICENSE).
