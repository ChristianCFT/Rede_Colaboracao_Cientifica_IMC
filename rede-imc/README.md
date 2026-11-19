# Rede de Colaboração IMC/UNIFEI

Visualização interativa da rede de colaboração dos pesquisadores do IMC (Instituto de Matemática e Computação) com os demais institutos da UNIFEI.

- **Backend:** FastAPI + Pandas + NetworkX. Lê os 4 CSVs, calcula a rede e o layout e expõe 2 rotas de leitura.
- **Frontend:** TypeScript + Canvas 2D + d3-force, empacotado com Vite.

```
.
├── backend/    API (FastAPI), dados e mineração (backend/mineracao)
└── frontend/   Interface (Vite + TypeScript)
```

## Requisitos

| Ferramenta | Versão |
|---|---|
| Python | 3.10 ou superior |
| Node.js | 18 ou superior (inclui o npm) |

## Como executar

São dois processos: o backend na porta **8000** e o frontend na porta **5173**. Use dois terminais.

### 1. Gerar os dados (mineração)

A mineração fica em `backend/mineracao/` e usa o mesmo `.venv` do backend (veja o passo 2 para criá-lo).
Coloque o ZIP dos currículos em `backend/mineracao/dados/brutos/Professores_v8.zip` e rode, de dentro de `backend/`:

```bash
python mineracao/main.py
```

Leva cerca de 70 s e grava os 4 CSVs direto em `backend/data/raw/`:

```
backend/data/raw/
├── dataset_completo_UNIFEI.csv
├── dataset_entrada_IMC.csv
├── dataset_saida_IMC.csv
└── dataset_atividades_IMC.csv
```

Os nomes precisam ser exatamente esses. A aplicação só lê os arquivos; nunca os altera.

### 2. Backend

```bash
cd backend

python -m venv .venv
source .venv/bin/activate          # Windows (PowerShell): .venv\Scripts\Activate.ps1
pip install -r requirements.txt

python -m uvicorn src.main:app --port 8000
```

> Rode sempre de dentro de `backend/` (a pasta que contém `src/`) e use `python -m uvicorn`, não só `uvicorn`: assim o servidor usa o Python do `.venv`. O módulo é `src.main`.

- A **primeira inicialização leva cerca de 50 s**: é o cálculo do layout. Ele roda uma vez e fica em cache na memória; as requisições seguintes são imediatas.
- Quando o terminal mostrar `Application startup complete`, a API está pronta.
- Documentação interativa: <http://127.0.0.1:8000/docs>
- Para desenvolvimento, acrescente `--reload` (cada recarga refaz o cálculo de ~50 s).

### 3. Frontend

Em outro terminal:

```bash
cd frontend
npm install
npm run dev
```

Abra <http://localhost:5173>. O Vite encaminha as chamadas `/api` para `http://127.0.0.1:8000`, então não é preciso configurar CORS nem URL em desenvolvimento.

Se abrir a página antes do backend terminar de iniciar, aguarde e recarregue.

## API

Prefixo `/api/v1`. Só leitura (GET).

| Rota | Descrição |
|---|---|
| `GET /api/v1/graph` | Rede principal (nós e arestas), pesquisadores sem colaboração com o IMC (`sem_colaboracao`), atividades, paleta e dimensões |
| `GET /api/v1/nodes/{node_id}` | Detalhes de um pesquisador, com vizinhos. Atende a rede principal e os pesquisadores sem colaboração |

## Usando a interface

- **Filtros** na barra lateral: instituto, área, tipo de relação, dimensão, janela temporal e mínimo de atividades.
- **Rótulos:** "Mostrar rótulos dos pesquisadores do IMC" liga e desliga os nomes no grafo. Pesquisadores de outros institutos aparecem pelo tooltip e pelo painel de detalhes.
- **Exibição da rede → "Incluir pesquisadores sem colaboração com o IMC":** mostra, em anel ao redor da rede, os pesquisadores da UNIFEI que não colaboram diretamente com o IMC, agrupados por instituto. São só pontos, sem ligações entre eles. A rede principal não se move, e as estatísticas continuam contando só a rede principal.
- **Detalhes:** clique em um nó ou em uma aresta, ou use a busca.

## Testes

```bash
cd backend
pip install -r requirements-dev.txt
pytest
```

Os testes usam os CSVs reais em `backend/data/raw/` e demoram um pouco pelo mesmo motivo da inicialização (cálculo do layout).

Verificação de tipos do frontend:

```bash
cd frontend
npm run typecheck
```

## Build de produção

```bash
cd frontend
npm run build      # roda tsc e gera frontend/dist/
npm run preview    # serve o build localmente
```

Em produção, sirva `frontend/dist/` por qualquer servidor estático e aponte para a API de uma destas formas:

- **Mesmo domínio:** configure o servidor para encaminhar `/api` ao backend. Não precisa mudar nada.
- **Domínio diferente:** defina `VITE_API_URL` antes do build (modelo em `frontend/.env.example`), por exemplo:
  ```bash
  VITE_API_URL=https://api.exemplo.com/api/v1 npm run build
  ```
  e libere a origem do frontend no backend com `CORS_ORIGINS`:
  ```bash
  CORS_ORIGINS=https://app.exemplo.com python -m uvicorn src.main:app --host 0.0.0.0 --port 8000
  ```

## Variáveis de ambiente

| Variável | Onde | Padrão | Uso |
|---|---|---|---|
| `VITE_API_URL` | frontend (build) | `/api/v1` | URL base da API |
| `CORS_ORIGINS` | backend | `http://localhost:5173,http://127.0.0.1:5173` | Origens permitidas, separadas por vírgula |

## Problemas comuns

| Sintoma | Causa provável | O que fazer |
|---|---|---|
| Backend falha ao iniciar citando arquivo não encontrado | CSV ausente ou com nome diferente | Confira os 4 nomes em `backend/data/raw/` |
| Página abre sem grafo, ou erro de rede no console | Backend ainda calculando o layout, ou fora do ar | Espere o `Application startup complete` e recarregue |
| `No module named 'fastapi'` | O comando `uvicorn` aberto é o do sistema, fora do `.venv` | Ative o `.venv`, rode `pip install -r requirements.txt` e use `python -m uvicorn ...` |
| `No module named 'src'` ou `'app'` | Pasta errada ou módulo errado | Rode de dentro de `backend/` com `src.main:app` |
| Falha ao instalar `pandas`/`scipy` | Python muito novo (ex.: 3.14) sem pacotes prontos | Crie o venv com Python 3.12 ou 3.13 |
| `Address already in use` | Porta 8000 ou 5173 ocupada | Use `--port` no uvicorn (e ajuste o proxy em `frontend/vite.config.ts`), ou encerre o outro processo |
| `pytest` não encontra os módulos | Executado fora de `backend/` | Rode de dentro da pasta `backend` |
| Alguns nomes aparecem com "�" | O caractere já vem quebrado nos CSVs de origem | Corrija na fonte; a aplicação não altera os dados |

## Estrutura do código

```
backend/src/
├── main.py            aplicação FastAPI
├── config.py          caminhos, colunas, paleta e regras de área
├── routes/            definição das rotas
├── controllers/       camada HTTP
├── services/          regras da aplicação
├── schemas/           modelos Pydantic
└── engine/            leitura dos CSVs, grafo e layout

frontend/src/
├── main.ts            ponto de entrada
├── api/               cliente HTTP e DTOs
├── core/              tipos, modelo, estado, seletores
├── graph/             física, renderização (canvas) e interação
├── ui/                barra lateral, painel de detalhes, HUD
└── styles/            CSS dividido por responsabilidade
```
