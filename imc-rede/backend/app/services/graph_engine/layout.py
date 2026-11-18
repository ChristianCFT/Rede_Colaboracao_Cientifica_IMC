"""Dois layouts pré-calculados: livre (por conexões) e separado por área (IMC ancorado)."""
import math
import networkx as nx

SC = 2000
CENTROS = {'Computação': (-.8, 0), 'Matemática': (.8, 0), 'Ambas': (0, 0), 'Outras': (0, -.9), 'Sem área': (0, -.9)}

def _grafo(nos, arestas):
    G = nx.Graph(); G.add_nodes_from(nos); G.add_edges_from(arestas); return G

def _escala(p):
    return {k: (float(v[0]) * SC, float(v[1]) * SC) for k, v in p.items()}

def livre(nos, arestas):
    return _escala(nx.spring_layout(_grafo(nos, arestas), k=.18, iterations=300, seed=7))

def por_area(nos, arestas):
    por = {}
    for k, v in nos.items():
        if v['instituto'] == 'IMC':
            por.setdefault(v['grupo'], []).append(k)
    ini = {}
    for g, ids in por.items():
        cx, cy = CENTROS[g]
        for i, k in enumerate(ids):
            ang = 2 * math.pi * i / len(ids)
            ini[k] = (cx + .55 * math.cos(ang), cy + .55 * math.sin(ang))
    return _escala(nx.spring_layout(_grafo(nos, arestas), k=.18, iterations=300, seed=7, pos=ini, fixed=list(ini)))
