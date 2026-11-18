# IMC Rede — full-stack (FastAPI + Vite/TypeScript)

## Árvore de diretórios

```
imc-rede/
├── backend/
│   ├── requirements.txt · requirements-dev.txt · pytest.ini
│   ├── tests/{test_areas,test_api}.py
│   ├── data/raw/                       # os 4 CSVs de entrada
│   └── app/
│       ├── main.py                     # FastAPI, CORS, handlers globais de exceção, /health
│       ├── core/config.py              # caminhos, paleta, REGRAS_AREA (Computação × Matemática), CORS
│       ├── schemas/graph.py            # Pydantic: Node, Edge, Graph, NetworkMetrics, Area, GraphFilter, NodeDetail
│       ├── services/graph_engine/
│       │   ├── loaders.py              # CSV → nós/arestas
│       │   ├── areas.py                # classificação Computação/Matemática
│       │   ├── layout.py               # layout livre e separado por área (NetworkX/SciPy)
│       │   ├── exporters.py            # GEXF / GraphML
│       │   └── engine.py               # Engine + @lru_cache: processa uma vez, serve schemas, filtros e detalhes
│       └── api/v1/
│           ├── router.py
│           └── endpoints/{graph,nodes,export}.py
└── frontend/
    ├── index.html                      # 3 colunas: sidebar · canvas (HUD + controles) · painel de detalhes
    ├── css/style.css                   # mesma identidade visual; tokens claros/escuros em variáveis CSS
    ├── package.json · tsconfig.json (strict) · vite.config.ts (proxy /api → :8000) · .env.example
    └── src/
        ├── main.ts                     # orquestração + tela de loading/erro
        ├── types/graph.ts              # DTOs da API + modelo de cliente
        ├── services/api.ts             # fetch tipado, ApiError
        ├── core/
        │   ├── dom.ts                  # $, esc e formatação pt-BR (1.486 · 3,8 · 47%)
        │   ├── model.ts                # nós, arestas, atividades indexadas (dimensão + ano)
        │   ├── state.ts                # estado da UI, filtros e barramento de eventos
        │   ├── selectors.ts            # recorte memoizado: arestas/nós visíveis, facetas, KPIs, tamanhos
        │   ├── betweenness.ts          # Brandes (exato) + betweenness.worker.ts (Web Worker)
        │   └── actions.ts              # selecionar nó/aresta, modo ego
        ├── canvas/
        │   ├── render.ts               # desenho, holofote no hover, exportação PNG
        │   ├── labels.ts               # rotulagem inteligente (zoom semântico + colisão)
        │   ├── camera.ts               # zoom/enquadrar/centralizar animados
        │   ├── physics.ts              # d3-force ancorado no layout do backend (pausar/retomar, arrastar)
        │   └── interaction.ts          # pan, zoom, hover, clique, arrastar nós, atalhos
        └── ui/
            ├── sidebar/                # accordion · facets (checkbox mestre) · sliders · display · search · filterSummary
            ├── hud.ts                  # KPIs no topo do canvas
            ├── cameraControls.ts       # botões flutuantes
            └── details/                # summaryView · nodeView · edgeView · parts
```

## Como rodar

```bash
# terminal 1 — API (http://127.0.0.1:8000, docs em /docs)
cd backend && python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# terminal 2 — interface (http://localhost:5173)
cd frontend && npm install && npm run dev
```

O primeiro start do backend leva alguns segundos (layouts spring + centralidades); depois tudo vem do cache em memória.

## Endpoints (`/api/v1`)

| Rota | O que faz |
|---|---|
| `GET /graph` | grafo completo: nós (com posições dos 2 layouts, centralidade de grau e intermediação), arestas, atividades, áreas, métricas |
| `GET /graph/filter?grupos=Matemática&tipos=IMC-IMC&peso_min=2&centralidade_min=0.01&incluir_externos=false` | mesmo formato, filtrado no servidor |
| `GET /nodes/{id}` | pesquisador + vizinhos + atividades em comum |
| `GET /export/{gexf\|graphml}` | download sob demanda (arquivo cacheado em `backend/.cache/`) |

## Plano de migração

1. **Backup**: mantenha o zip antigo (`web/` + `pipeline/`) até o passo 6.
2. **Backend isolado**: suba só o FastAPI e compare `/graph` com o antigo `graph-data.js` (1486 nós, 2828 arestas, 3078 atividades, 16 Computação / 23 Matemática).
3. **Frontend em paralelo**: `npm run dev` com o proxy; a identidade visual é a mesma (ver “Interface” abaixo).
4. **Paridade**: confira filtros por tipo/área, os dois layouts, cor por área, clique em nó/aresta, busca e PNG.
5. **Exports**: baixe `/export/gexf` e `/export/graphml` e compare com `exports/` antigos.
6. **Corte**: apague `web/`, `pipeline/` e `build.py` antigos.
7. **Testes**: `cd backend && pip install -r requirements-dev.txt && pytest` (cobre áreas, grafo completo, filtros, detalhe/404 e exports).

## Decisões e limites

- O painel lateral busca a lista de conexões em `GET /nodes/{id}` (mesmo markup; se a API falhar, mantém a lista local).
- Os filtros da barra lateral continuam rodando no navegador, para a interação seguir instantânea e idêntica. `GET /graph/filter` está pronto para uso por outros clientes ou para grafos maiores.
- CORS configurável por variável de ambiente: `CORS_ORIGINS="http://localhost:5173,https://meu-site"`.
- Verificado nesta versão: `tsc --strict`, `vite build`, `pytest` (12 testes) e a interface rodando no Chromium contra o FastAPI real; os contadores filtrados foram conferidos contra um cálculo independente em Python.

## Interface (evolução de UI/UX)

Mesma linguagem visual (tema escuro `#121212` no canvas, `#1e1e1e`/`#22252a` nas barras, controles azuis
nativos, nós circulares e rótulos brancos), com estas mudanças:

**Barra lateral**
- Seções em acordeão com chevron. Abertas por padrão: *Dimensões*, *Janela temporal* e *Tipo de relação*;
  recolhidas: *Área do IMC*, *Cores e layout* e *Exibição*. A escolha fica salva no navegador.
- Checkbox mestre tri-state (marcado / desmarcado / indeterminado) em *Tipo de relação* e *Área do IMC*.
- **Dimensões de colaboração**: Artigos científicos, Projetos de pesquisa, Orientações, Bancas e Produção
  técnico-tecnológica (as 5 camadas que existem nos dados: art, prj, ori, ban, ptt).
- **Janela temporal**: slider duplo de anos (1989–2026 nos dados) com o mesmo visual do slider
  “Mín. de atividades em comum”. A atividade de ano inválido (2074) só entra quando a janela cobre todo o período.
- **Tamanho do nó**: grau (parceiros no recorte), volume de produções (atividades distintas no recorte) ou
  intermediação (betweenness exato no recorte, calculado num Web Worker).
- **Isolar rede (1º e 2º graus)**: aparece abaixo da busca quando há um pesquisador selecionado.
- A legenda redundante saiu; o subtítulo mostra os filtros ativos com um atalho “Limpar”.
- Contadores em tempo real, no padrão de busca facetada (cada lista ignora o próprio filtro):
  dimensões = atividades distintas, tipos = arestas, áreas = pesquisadores do IMC com conexões.

**Canvas**
- Rótulos sem sobreposição: zoom semântico decide quem é candidato e uma grade de colisão posiciona cada
  rótulo em até 4 posições (direita, esquerda, acima, abaixo) ou o omite.
- Holofote no hover: o nó, os vizinhos e as arestas entre eles a 100%, o resto a ~10%, com os nomes dos vizinhos.
- HUD de KPIs: pesquisadores visíveis, conexões ativas, dimensão predominante e grau médio do recorte.
- Controles flutuantes: aproximar, afastar, ajustar à tela, pausar/retomar física e exportar PNG.
- Física leve (d3-force) ancorada no layout do backend: separa nós encavalados, permite arrastar nós
  (os orientandos de grau 1 acompanham o orientador) e anima a troca de layout.
- Atalhos: `Esc` limpa a seleção, `+`/`−` zoom, `F` enquadra, duplo clique no fundo enquadra.

**Painel direito**
- Sem seleção: resumo do recorte (5 mais conectados e distribuição por instituto).
- Pesquisador: instituto, área, barras das 5 dimensões no recorte, Top 5 parceiros (clique foca e seleciona;
  o número abre as colaborações em comum), vetor de produção do Lattes e a lista completa de conexões.
- Aresta: todas as colaborações da dupla agrupadas por dimensão, da mais recente para a mais antiga;
  as que estão fora do recorte atual aparecem esmaecidas.

**Desempenho**: o recorte (≈4 ms para o grafo completo) é memoizado pela versão dos filtros; hover, câmera
e física só redesenham. A física roda a 60 fps e o betweenness não bloqueia a interface.
