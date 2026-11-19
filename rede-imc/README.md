# Rede de Colaboração Científica · IMC/UNIFEI

Visualização interativa de **quem colabora com quem** no Instituto de Matemática e Computação (IMC) da UNIFEI.
A rede é montada a partir dos currículos Lattes dos docentes e mostra como os pesquisadores do IMC se
relacionam entre si, com os outros institutos da UNIFEI e com pesquisadores externos.

Cada ligação da rede conta as atividades que a dupla fez junto, em cinco dimensões:

| Sigla | Dimensão |
|---|---|
| ART | Artigos científicos (periódicos e anais de congresso) |
| PRJ | Projetos de pesquisa |
| ORI | Orientações concluídas |
| BAN | Bancas acadêmicas |
| PTT | Produção técnico-tecnológica |

---

## Como funciona

O projeto tem três partes, que rodam **separadas e nesta ordem**:

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
  │  2. Backend     │   FastAPI: lê os CSVs, monta o grafo e calcula o layout
  └────────┬────────┘
           │ JSON em /api/v1
           ▼
  ┌─────────────────┐   npm run dev
  │  3. Frontend    │   desenha a rede no navegador (Canvas + d3-force)
  └─────────────────┘
```

| Parte | Tecnologias | Onde |
|---|---|---|
| Mineração | Python, BeautifulSoup, lxml | `backend/mineracao/` ([README próprio](backend/mineracao/README.md)) |
| Backend | Python, FastAPI, pandas, NetworkX | `backend/src/` |
| Frontend | TypeScript, Vite, Canvas 2D, d3-force | `frontend/src/` |

A mineração e o backend dividem o mesmo ambiente Python (`backend/.venv`) e o mesmo `requirements.txt`.

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
python -m venv .venv
source .venv/bin/activate        # Windows (PowerShell): .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Rodar a mineração

O ZIP dos currículos fica em `backend/mineracao/dados/brutos/Professores_v8.zip`. De dentro de `backend/`, com o `.venv` ativo:

```bash
python mineracao/main.py
```

Leva cerca de 70 segundos e grava os 4 CSVs em `backend/data/raw/`. Só é preciso rodar de novo quando os currículos mudarem.

### 3. Subir o backend

Ainda em `backend/`:

```bash
python -m uvicorn src.main:app --port 8000
```

- A primeira inicialização leva **cerca de 50 segundos** (cálculo do layout). Depois disso, as respostas são imediatas.
- A API está pronta quando aparecer `Application startup complete`.
- Documentação interativa: <http://127.0.0.1:8000/docs>

### 4. Subir o frontend

No outro terminal:

```bash
cd frontend
npm install
npm run dev
```

Abra <http://localhost:5173>. O Vite encaminha as chamadas `/api` para o backend na porta 8000, então não é preciso configurar nada.

---

## Usando a interface

| Onde | O que faz |
|---|---|
| **Buscar pesquisador** | Encontra alguém pelo nome e centraliza a rede nele |
| **Dimensões de colaboração** | Liga e desliga ART, PRJ, ORI, BAN e PTT |
| **Janela temporal** | Considera só as atividades de um intervalo de anos |
| **Tipo de relação** | Filtra as ligações (IMC–IMC, IMC–outro instituto, IMC–externo) |
| **Área do IMC** | Computação, Matemática ou ambas |
| **Exibição da rede** | Mostra, em anel ao redor da rede, os pesquisadores da UNIFEI que não colaboram com o IMC |
| **Cores e layout** | Cor por instituto ou por área; layout livre ou separado por área |
| **Exibição** | Rótulos do IMC, externos (EXT) e mínimo de atividades em comum |
| **Clique em um nó** | Painel com as 5 dimensões, os principais parceiros e as conexões |
| **Clique em uma ligação** | Lista todas as atividades da dupla, por dimensão e ano |
| **Peso da colaboração** (canto inferior esquerdo, tecla P) | Liga o modo peso, explicado abaixo |

Os indicadores no topo (HUD) sempre se referem à rede principal do IMC.

### Modo peso

Desligado, a rede usa a contagem de atividades em comum, sem normalização. Ligado, cada ligação passa
a ter um **peso de 0 a 1**, calculado como na proposta metodológica:

- cada dimensão vira `ln(1 + x) / ln(1 + maior valor da rede)`;
- o peso é a soma ponderada: Artigos 0,40 · Projetos 0,20 · Orientações 0,20 · Produção técnica 0,15 · Bancas 0,05.

Os maiores valores vêm da rede inteira e não mudam com os filtros. Desligar uma dimensão ou estreitar a
janela temporal recalcula o peso só com as atividades visíveis, na mesma escala. No modo peso:

- **espessura da ligação** = peso, pela raiz de peso ÷ maior peso da rede, para que as ligações fracas
  continuem visíveis. As mais fortes são desenhadas por cima, e a legenda mostra três espessuras de referência;
- **clique em uma ligação**: o peso, a posição entre as ligações visíveis e como o peso é calculado.
  O vetor e as atividades não aparecem;
- **clique em um nó**: os parceiros ordenados pelo peso da relação com cada um;
- **sem seleção**: as ligações mais fortes.

Os α ficam em `backend/src/config.py` (`ALFAS`) e a fórmula em `backend/src/engine/peso.py`. O frontend
usa a mesma fórmula em `frontend/src/core/peso.ts`, para recalcular o peso no recorte.

---

## API

Prefixo `/api/v1`. Somente leitura (GET).

| Rota | Retorna |
|---|---|
| `GET /api/v1/graph` | A rede inteira: nós, ligações (com `peso`), pesquisadores sem colaboração, atividades, paleta, dimensões e os parâmetros do peso (`alfas`, `referencias`) |
| `GET /api/v1/nodes/{node_id}` | Detalhes de um pesquisador e seus vizinhos, com o `peso` de cada relação (404 se não existir) |

---

## Estrutura do projeto

```
rede-imc/
├── .gitignore
├── backend/
│   ├── requirements.txt          dependências da API e da mineração
│   ├── data/raw/                 os 4 CSVs gerados pela mineração (entrada da API)
│   ├── mineracao/                mineração dos currículos Lattes
│   │   ├── main.py               executa as 6 etapas
│   │   ├── configuracao.py       caminhos, siglas e limiares
│   │   ├── src/                  módulos de cada etapa
│   │   └── dados/brutos/         ZIP dos currículos
│   └── src/                      API
│       ├── main.py               aplicação FastAPI
│       ├── config.py             caminhos, colunas, paleta, regras de área e α do peso
│       ├── routes/               definição das rotas
│       ├── controllers/          camada HTTP (erros → status)
│       ├── services/             regras da aplicação
│       ├── schemas/              modelos Pydantic
│       └── engine/               leitura dos CSVs, grafo NetworkX, layout e peso das ligações
└── frontend/
    ├── index.html
    ├── vite.config.ts            proxy /api → backend
    └── src/
        ├── main.ts               ponto de entrada
        ├── api/                  cliente HTTP e contratos
        ├── core/                 tipos, modelo, estado e filtros
        ├── graph/                física, desenho no canvas e interação
        ├── ui/                   barra lateral, painel de detalhes e HUD
        └── styles/               CSS por responsabilidade
```

---

## O que vai para o Git

| Caminho | Vai para o repositório? |
|---|---|
| `backend/mineracao/dados/brutos/` (ZIP dos currículos) | Sim |
| `backend/data/raw/` (CSVs gerados) | Sim |
| `backend/mineracao/dados/temporarios/` (extração do ZIP) | Não |
| `.venv/`, `__pycache__/`, `frontend/node_modules/`, `frontend/dist/` | Não |

As regras estão no [`.gitignore`](.gitignore).

---

## Produção

```bash
cd frontend
npm run build      # gera frontend/dist/
npm run preview    # testa o build localmente
```

Sirva `frontend/dist/` em qualquer servidor estático e ligue o frontend à API de um destes jeitos:

- **Mesmo domínio:** encaminhe `/api` para o backend. Não precisa mudar nada.
- **Domínios diferentes:** troque `VITE_API_URL` em `frontend/.env` (ou passe a variável no comando do build) e libere a origem no backend:
  ```bash
  VITE_API_URL=https://api.exemplo.com/api/v1 npm run build
  ```
  ```bash
  CORS_ORIGINS=https://app.exemplo.com python -m uvicorn src.main:app --host 0.0.0.0 --port 8000
  ```

| Variável | Onde | Padrão | Para que serve |
|---|---|---|---|
| `VITE_API_URL` | `frontend/.env` (lido pelo Vite no dev e no build) | `/api/v1` | Endereço da API |
| `CORS_ORIGINS` | backend | `http://localhost:5173,http://127.0.0.1:5173` | Origens permitidas, separadas por vírgula |

