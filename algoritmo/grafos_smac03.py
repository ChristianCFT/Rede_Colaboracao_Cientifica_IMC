#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
grafos_smac03.py - algoritmos da disciplina SMAC03 (Grafos, UNIFEI), organizados por aula.

Cada seção segue a ordem do material do Prof. Rafael Frinhani:
  Aula 2 - Conceitos de Teoria dos Grafos   (grau, densidade, lista de adjacência)
  Aula 2 - Percurso e Conectividade          (componentes conexos, pontos de articulação, pontes)
  Aula 2 - Busca em Grafos                   (BFS, DFS, classificação de arestas)
  Aula 3 - Ordenação Topológica e Coloração  (coloração gulosa, bipartição)
  Aula 4 - Caminho Mínimo                    (Dijkstra)

Os algoritmos são implementados aqui, sem caixa-preta. A função verificar() compara cada
resultado com o networkx, para garantir que a implementação está correta.

Representação: grafo = dict {vértice: {vizinho: peso}} (lista de adjacência com pesos).
Grafo não direcionado: cada aresta aparece nos dois sentidos.
"""
import heapq
from collections import deque

INF = float('inf')


# =============================================================================
# AULA 2 - CONCEITOS: grau, densidade e lista de adjacência
# =============================================================================
def de_arestas(arestas):
    """Constrói a lista de adjacência a partir de (u, v, peso) não direcionadas."""
    G = {}
    for u, v, w in arestas:
        G.setdefault(u, {})[v] = w
        G.setdefault(v, {})[u] = w
    return G


def grau(G, v):
    return len(G[v])


def densidade(G):
    """Razão entre o nº de arestas e o máximo possível: m / (n(n-1)/2)."""
    n = len(G)
    m = sum(len(G[v]) for v in G) // 2
    return m / (n * (n - 1) / 2) if n > 1 else 0.0


def handshake(G):
    """Lema do aperto de mãos: soma dos graus = 2m. Retorna (soma, 2m)."""
    return sum(len(G[v]) for v in G), 2 * (sum(len(G[v]) for v in G) // 2)


# =============================================================================
# AULA 2 - BUSCA EM LARGURA (BFS) - base de componentes e de distância não ponderada
# (MATÉRIA: Busca em Largura - níveis da busca; vértices brancos, cinzas e pretos)
# =============================================================================
def bfs(G, s):
    """Retorna (distância em arestas, pai, ordem de visita) a partir de s."""
    dist = {s: 0}
    pai = {s: None}
    ordem = [s]
    fila = deque([s])
    while fila:
        u = fila.popleft()
        for v in sorted(G[u]):
            if v not in dist:
                dist[v] = dist[u] + 1
                pai[v] = u
                ordem.append(v)
                fila.append(v)
    return dist, pai, ordem


def componentes(G):
    """Componentes conexos por BFS. Retorna lista de conjuntos, do maior para o menor."""
    visto = set()
    comps = []
    for s in sorted(G):
        if s in visto:
            continue
        dist, _, _ = bfs(G, s)
        visto |= set(dist)
        comps.append(set(dist))
    return sorted(comps, key=len, reverse=True)


# =============================================================================
# AULA 2 - BUSCA EM PROFUNDIDADE (DFS) E CLASSIFICAÇÃO DE ARESTAS
# (MATÉRIA: Tempo de descoberta td[v] e término tt[v]; árvore, retorno, avanço, cruzamento)
# Em grafo não direcionado só existem arestas de árvore e de retorno.
# =============================================================================
def dfs(G):
    """DFS iterativa (evita limite de recursão). Retorna td, tt, pai e classificação das arestas."""
    cor = {v: 'branco' for v in G}
    td, tt, pai = {}, {}, {}
    tipo = {}
    t = 0
    for r in sorted(G):
        if cor[r] != 'branco':
            continue
        cor[r] = 'cinza'
        td[r] = t
        t += 1
        pai[r] = None
        pilha = [(r, iter(sorted(G[r])))]
        while pilha:
            u, it = pilha[-1]
            v = next(it, None)
            if v is None:
                cor[u] = 'preto'
                tt[u] = t
                t += 1
                pilha.pop()
                continue
            if cor[v] == 'branco':
                pai[v] = u
                cor[v] = 'cinza'
                td[v] = t
                t += 1
                tipo[frozenset((u, v))] = 'arvore'
                pilha.append((v, iter(sorted(G[v]))))
            elif cor[v] == 'cinza' and v != pai[u]:
                tipo.setdefault(frozenset((u, v)), 'retorno')
    return td, tt, pai, tipo


# =============================================================================
# AULA 2 - CONECTIVIDADE: PONTOS DE ARTICULAÇÃO E PONTES (Tarjan, via DFS)
# (MATÉRIA: Articulação (vértice, aresta); "elo de ligação" = ponto de articulação)
# =============================================================================
def articulacao_e_pontes(G):
    """Retorna (pontos de articulação, pontes). Usa low-point por DFS iterativa."""
    disc, low, pai = {}, {}, {}
    art = set()
    pontes = []
    t = 0
    for r in sorted(G):
        if r in disc:
            continue
        disc[r] = low[r] = t
        t += 1
        pai[r] = None
        filhos_raiz = 0
        pilha = [(r, iter(sorted(G[r])))]
        while pilha:
            u, it = pilha[-1]
            v = next(it, None)
            if v is None:
                pilha.pop()
                p = pai[u]
                if p is None:
                    continue
                low[p] = min(low[p], low[u])
                if low[u] > disc[p]:
                    pontes.append(tuple(sorted((p, u))))
                if p == r:
                    filhos_raiz += 1
                elif low[u] >= disc[p]:
                    art.add(p)
                continue
            if v not in disc:
                pai[v] = u
                disc[v] = low[v] = t
                t += 1
                pilha.append((v, iter(sorted(G[v]))))
            elif v != pai[u]:
                low[u] = min(low[u], disc[v])
        if filhos_raiz > 1:
            art.add(r)
    return art, sorted(pontes)


# =============================================================================
# AULA 3 - COLORAÇÃO DE VÉRTICES E BIPARTIÇÃO
# (MATÉRIA: número cromático; algoritmo guloso; grafo bipartido por 2-coloração com BFS)
# =============================================================================
def coloracao_gulosa(G):
    """Coloração gulosa com ordem por grau decrescente (Welsh-Powell).
    Retorna (cores por vértice, número de cores usadas). Dá um limite superior de χ(G)."""
    ordem = sorted(G, key=lambda v: (-len(G[v]), v))
    cor = {}
    for v in ordem:
        usadas = {cor[u] for u in G[v] if u in cor}
        c = 0
        while c in usadas:
            c += 1
        cor[v] = c
    return cor, (max(cor.values()) + 1 if cor else 0)


def bipartido(G):
    """Testa se G é bipartido por BFS com 2 cores. Retorna (bool, partição ou None)."""
    cor = {}
    for s in sorted(G):
        if s in cor:
            continue
        cor[s] = 0
        fila = deque([s])
        while fila:
            u = fila.popleft()
            for v in G[u]:
                if v not in cor:
                    cor[v] = 1 - cor[u]
                    fila.append(v)
                elif cor[v] == cor[u]:
                    return False, None
    return True, cor


# =============================================================================
# AULA 4 - CAMINHO MÍNIMO: DIJKSTRA (pesos não negativos)
# (MATÉRIA: algoritmo guloso; relaxamento de arestas; fila de prioridade)
# =============================================================================
def dijkstra(G, s, custo=lambda w: w):
    """Distância e pai do caminho mínimo de s. custo(w) transforma o peso da aresta."""
    dist = {v: INF for v in G}
    pai = {v: None for v in G}
    dist[s] = 0.0
    heap = [(0.0, s)]
    feitos = set()
    while heap:
        d, u = heapq.heappop(heap)
        if u in feitos:
            continue
        feitos.add(u)
        for v, w in G[u].items():
            nd = d + custo(w)
            if nd < dist[v]:
                dist[v] = nd
                pai[v] = u
                heapq.heappush(heap, (nd, v))
    return dist, pai


def caminho(pai, destino):
    """Reconstrói o caminho até destino a partir do vetor de pais."""
    if pai.get(destino) is None and destino not in pai:
        return []
    c = [destino]
    while pai[c[-1]] is not None:
        c.append(pai[c[-1]])
    return c[::-1]


# =============================================================================
# VERIFICAÇÃO CONTRA O NETWORKX (usada pelo imc_examina e para checar esta implementação)
# =============================================================================
def verificar(G, peso_nx=None):
    """Compara cada algoritmo com o networkx. Imprime OK/ERRO e retorna True se tudo bate."""
    import networkx as nx
    H = nx.Graph()
    H.add_nodes_from(G)
    for u in G:
        for v, w in G[u].items():
            H.add_edge(u, v, weight=w)
    ok = True

    def conf(nome, a, b):
        nonlocal ok
        resultado = (a == b)
        ok &= resultado
        print(f'   {nome:<34} {"OK" if resultado else "ERRO"}')

    comp_nx = sorted((frozenset(c) for c in nx.connected_components(H)), key=len, reverse=True)
    comp_me = [frozenset(c) for c in componentes(G)]
    conf('componentes conexos (BFS)', sorted(map(sorted, comp_me)), sorted(map(sorted, comp_nx)))

    art_nx = set(nx.articulation_points(H))
    pon_nx = sorted(tuple(sorted(e)) for e in nx.bridges(H))
    art_me, pon_me = articulacao_e_pontes(G)
    conf('pontos de articulação (Tarjan)', art_me, art_nx)
    conf('pontes (Tarjan)', pon_me, pon_nx)

    s = sorted(G)[0]
    d_me, _ = dijkstra(G, s)
    d_nx = nx.single_source_dijkstra_path_length(H, s)
    def igual(x, y):
        return x == y or abs(x - y) < 1e-9   # inf == inf também conta como igual
    conf('Dijkstra (distâncias de um vértice)',
         all(igual(d_me[v], d_nx.get(v, INF)) for v in G), True)

    cor, k = coloracao_gulosa(G)
    conf('coloração gulosa é própria', all(cor[u] != cor[v] for u in G for v in G[u]), True)
    bip_me, _ = bipartido(G)
    conf('bipartição (2-coloração)', bip_me, nx.is_bipartite(H))
    return ok

