# Rede de Colaboração Científica · IMC/UNIFEI

Visualização interativa de **quem colabora com quem** no Instituto de Matemática e Computação (IMC) da
UNIFEI. A rede é montada a partir dos currículos Lattes dos docentes e mostra como os pesquisadores do
IMC se relacionam entre si, com as outras unidades da UNIFEI e com pesquisadores de fora.

---

## Como funciona

O projeto tem três partes, que rodam separadas e nesta ordem:

```
  Currículos Lattes (ZIP)
          │
          ▼
  ┌─────────────────┐   python mineracao/main.py
  │  1. Mineração   │   lê os HTMLs e monta a rede
  └────────┬────────┘
           │ grava 4 CSVs
           ▼
     backend/data/raw/
           │
           ▼
  ┌─────────────────┐   python -m uvicorn src.main:app
  │  2. Backend     │   lê os CSVs, monta o grafo, calcula pesos e posições
  └────────┬────────┘
           │ JSON em /api/v1
           ▼
  ┌─────────────────┐   npm run dev
  │  3. Frontend    │   desenha a rede no navegador
  └─────────────────┘
```

| Parte | Tecnologias | Onde |
|---|---|---|
| Mineração | Python, BeautifulSoup, lxml | `backend/mineracao/` ([README próprio](backend/mineracao/README.md)) |
| Backend | Python, FastAPI, pandas, NetworkX, SciPy | `backend/src/` |
| Frontend | TypeScript, Vite, Canvas 2D, d3-force | `frontend/src/` |

A mineração e o backend usam o mesmo ambiente Python (`backend/.venv`) e o mesmo `requirements.txt`.

---

## O modelo da rede

- **Vértice** é um pesquisador: docente do IMC, docente de outra unidade da UNIFEI ou pesquisador externo.
- **Aresta** é uma colaboração entre dois pesquisadores. O pesquisador 1 é sempre do IMC.
- Cada aresta guarda as atividades que a dupla fez junto, em cinco dimensões:

| Sigla | Dimensão |
|---|---|
| ART | Artigos científicos (periódicos e anais de congresso) |
| PRJ | Projetos de pesquisa |
| ORI | Orientações concluídas, orientadas em conjunto |
| BAN | Bancas acadêmicas, como avaliadores |
| PTT | Produção técnico-tecnológica |

- O **tipo de relação** diz quem é o parceiro: `IMC-IMC`, `IMC-<unidade>` (IFQ, IEM…) ou `IMC-EXT`.
- Docentes da UNIFEI sem relação com o IMC aparecem só como pontos, num anel ao redor da rede.

### Peso da colaboração

Cada relação tem um peso de 0 a 1, calculado a partir do vetor de contagens:

- cada dimensão vira `z = ln(1 + x) / ln(1 + M)`, em que `M` é o maior valor daquela dimensão na rede;
- o peso é `W = Σ α · z`, com α: Artigos 0,40 · Projetos 0,20 · Orientações 0,20 · Produção técnica 0,15 · Bancas 0,05.

Os valores `M` são calculados uma vez, sobre todas as relações. Com filtros ativos, o peso é recalculado
só com as atividades visíveis, mas com os mesmos `M`. Os α ficam em `backend/src/config.py` (`ALFAS`),
a fórmula em `backend/src/engine/peso.py`, e o frontend repete a mesma fórmula em `frontend/src/core/peso.ts`.

---

## Requisitos

- **Python** 3.10 ou superior
- **Node.js** 18 ou superior (já vem com o npm)

---

## Como executar

Use dois terminais: um para o backend e outro para o frontend.

### 1. Preparar o ambiente Python (só na primeira vez)

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate        # Windows (PowerShell): .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Rodar a mineração

Só é preciso quando os currículos mudarem. De dentro de `backend/`, com o `.venv` ativo:

```bash
python mineracao/main.py
```

Leva cerca de 70 segundos e grava os 4 CSVs em `backend/data/raw/`.

### 3. Subir o backend

Ainda em `backend/`:

```bash
python -m uvicorn src.main:app --port 8000
```

- A inicialização leva cerca de 50 segundos (cálculo das posições). Depois disso, as respostas são imediatas.
- A API está pronta quando aparecer `Application startup complete`.
- Documentação interativa: <http://127.0.0.1:8000/docs>

### 4. Subir o frontend

No outro terminal:

```bash
cd frontend
npm install
npm run dev
```

Abra <http://localhost:5173>. O Vite encaminha as chamadas `/api` para o backend na porta 8000.

---

## Usando a interface

A tela tem três áreas: filtros à esquerda, o grafo no centro e os detalhes à direita.

| Onde | O que faz |
|---|---|
| **Buscar pesquisador** | Encontra alguém pelo nome e centraliza a rede nele |
| **Dimensões de colaboração** | Liga e desliga ART, PRJ, ORI, BAN e PTT |
| **Janela temporal** | Considera só as atividades de um intervalo de anos |
| **Tipo de relação** | Filtra as arestas (IMC-IMC, IMC-outra unidade, IMC-externo) |
| **Área do IMC** | Computação, Matemática ou outras |
| **Exibição da rede** | Mostra o anel dos docentes da UNIFEI sem colaboração com o IMC |
| **Cores e layout** | Cor por instituto ou por área; layout livre ou separado por área |
| **Exibição** | Rótulos do IMC, externos e mínimo de atividades em comum |
| **Clique em um nó** | Painel com as dimensões, os principais parceiros e todas as conexões |
| **Clique em uma aresta** | Todas as atividades da dupla, por dimensão e ano |
| **Peso da colaboração** (canto inferior esquerdo, tecla P) | Liga o modo peso |

- **Modo contagem** (padrão): a espessura da aresta acompanha o número de atividades em comum.
- **Modo peso**: a espessura e a intensidade da aresta acompanham o peso. As relações fortes ficam grossas
  e quase sólidas, e as fracas finas e claras. Os painéis passam a ordenar e mostrar os parceiros pelo peso.

Atalhos: `Esc` limpa a seleção, `+` e `−` dão zoom, `F` enquadra a rede, `P` liga ou desliga o modo peso.
Os indicadores no topo (HUD) sempre se referem à rede principal do IMC.

---

## API

Prefixo `/api/v1`. Somente leitura.

| Rota | Retorna |
|---|---|
| `GET /api/v1/graph` | A rede inteira: nós com posições, arestas com vetor e peso, pesquisadores sem colaboração, atividades, paleta e os parâmetros do peso |
| `GET /api/v1/nodes/{node_id}` | Detalhes de um pesquisador e seus vizinhos (404 se não existir) |

---

## Estrutura do projeto

```
rede-imc-unifei/
├── backend/
│   ├── requirements.txt          dependências da API e da mineração
│   ├── data/raw/                 os 4 CSVs gerados pela mineração (entrada da API)
│   ├── mineracao/                mineração dos currículos Lattes (ver README próprio)
│   └── src/                      API
│       ├── main.py               aplicação FastAPI
│       ├── config.py             caminhos, colunas, paleta, regras de área e α do peso
│       ├── routes/               rotas
│       ├── controllers/          camada HTTP (erros → status)
│       ├── services/             regras da aplicação
│       ├── schemas/              modelos Pydantic
│       └── engine/               leitura dos CSVs, grafo, layouts e peso
│           ├── loaders.py        lê os CSVs e monta vértices e arestas
│           ├── areas.py          classifica o IMC em Computação e Matemática
│           ├── layout.py         posições: livre, por área e anel
│           ├── peso.py           peso normalizado das relações
│           └── engine.py         calcula tudo uma vez e guarda em memória
└── frontend/
    ├── index.html
    ├── vite.config.ts            proxy /api → backend
    └── src/
        ├── main.ts               ponto de entrada
        ├── api/                  cliente HTTP e contratos
        ├── core/                 modelo, estado, filtros (recorte) e peso
        ├── graph/                desenho no canvas, física e interação
        ├── ui/                   barra lateral, painel de detalhes, HUD e chave do peso
        └── styles/               CSS por responsabilidade
```

O ZIP dos currículos (`backend/mineracao/dados/brutos/`) e os CSVs gerados (`backend/data/raw/`) vão
para o Git. A extração do ZIP, os ambientes (`.venv`, `node_modules`) e o build (`frontend/dist`) não.

---

## Produção

```bash
cd frontend
npm run build      # gera frontend/dist/
npm run preview    # testa o build localmente
```

Sirva `frontend/dist/` em qualquer servidor estático e ligue o frontend à API de um destes jeitos:

- **Mesmo domínio:** encaminhe `/api` para o backend.
- **Domínios diferentes:** defina o endereço da API no build e libere a origem no backend:
  ```bash
  VITE_API_URL=https://api.exemplo.com/api/v1 npm run build
  ```
  ```bash
  CORS_ORIGINS=https://app.exemplo.com python -m uvicorn src.main:app --host 0.0.0.0 --port 8000
  ```

| Variável | Onde | Padrão | Para que serve |
|---|---|---|---|
| `VITE_API_URL` | `frontend/.env` (lido pelo Vite) | `/api/v1` | Endereço da API |
| `CORS_ORIGINS` | backend | `http://localhost:5173,http://127.0.0.1:5173` | Origens permitidas, separadas por vírgula |
