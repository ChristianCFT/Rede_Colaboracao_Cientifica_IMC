# layouts pré-calculados: livre, por área e o anel dos sem colaboração
import itertools
import math

import networkx as nx
import numpy as np
from scipy.spatial import cKDTree

SC = 2000
CENTROS = {'Computação': (-.8, 0), 'Matemática': (.8, 0), 'Ambas': (0, 0), 'Outras': (0, -.9), 'Sem área': (0, -.9)}

# k do spring_layout
K_LIVRE = .8   # livre
K_AREA = .18   # por área (k alto espalha demais em volta do IMC fixo)

# mesma distância mínima da física do frontend (raio 4 x 5 = 20 por nó)
DISTANCIA_MINIMA = 40
PASSOS_AFASTAR = 400                   # máximo de rodadas
FRACAO_DO_EMPURRAO = .6                # menor que 1 pra não oscilar
FOLGA_ISOLADO = 2 * DISTANCIA_MINIMA   # espaço em volta de quem não tem relação
ANGULO_DOURADO = math.pi * (3 - math.sqrt(5))  # espiral

# anel dos sem colaboração
FOLGA = 140         # entre a rede e a primeira volta
VOLTAS = 3          # voltas do anel
ENTRE_VOLTAS = 90   # entre voltas
SETORES = 180       # resolução do contorno
ALCANCE = 12        # janela do máximo móvel
SUAVIZAR = 9        # janela da média (menor que ALCANCE)


def _spring(G, k, **kw):
    p = nx.spring_layout(G, k=k, iterations=300, seed=7, **kw)
    return {n: (float(v[0]) * SC, float(v[1]) * SC) for n, v in p.items()}


def livre(nos, G):
    """quem não tem relação fica perto do IMC"""
    # o spring_layout joga os isolados pra borda, então roda sem eles e encaixa depois
    ligados = G.subgraph([k for k in G if G.degree(k) > 0])
    pos = _afastar(_spring(ligados, K_LIVRE), set())
    for k in G:
        if G.degree(k) == 0:
            pos[k] = _perto_do_imc(nos, pos)
    return pos


def por_area(nos, G):
    # 'Outras' e 'Sem área' dividem o mesmo círculo (antes ficavam um em cima do outro)
    por = {}
    for k, v in nos.items():
        if v['instituto'] == 'IMC':
            por.setdefault(CENTROS[v['grupo']], []).append(k)
    ini = {}
    for (cx, cy), ids in por.items():
        for i, k in enumerate(ids):
            ang = 2 * math.pi * i / len(ids)
            ini[k] = (cx + .55 * math.cos(ang), cy + .55 * math.sin(ang))
    return _afastar(_spring(G, K_AREA, pos=ini, fixed=list(ini)), set(ini))


def _afastar(pos, fixos):
    """afasta os nós mais próximos que DISTANCIA_MINIMA (os fixos não mexem)"""
    ids = list(pos)
    P = np.array([pos[k] for k in ids], dtype=float)
    preso = np.array([k in fixos for k in ids])
    for _ in range(PASSOS_AFASTAR):
        pares = cKDTree(P).query_pairs(DISTANCIA_MINIMA * .999, output_type='ndarray')
        if not len(pares):
            break
        i, j = pares[:, 0], pares[:, 1]
        d = P[j] - P[i]
        dist = np.hypot(d[:, 0], d[:, 1])
        juntos = dist < 1e-9
        d[juntos] = np.column_stack([np.cos(i[juntos] * ANGULO_DOURADO), np.sin(i[juntos] * ANGULO_DOURADO)])
        dist[juntos] = 1.0
        empurrao = d / dist[:, None] * ((DISTANCIA_MINIMA - dist) / 2)[:, None]
        mov = np.zeros_like(P)
        np.add.at(mov, i, -empurrao)
        np.add.at(mov, j, empurrao)
        mov[preso] = 0
        P += FRACAO_DO_EMPURRAO * mov
    return {k: (float(x), float(y)) for k, (x, y) in zip(ids, P)}


def _perto_do_imc(nos, pos):
    """primeiro lugar livre numa espiral a partir do centro do IMC"""
    if not pos:
        return 0.0, 0.0
    imc = [p for k, p in pos.items() if nos[k]['instituto'] == 'IMC'] or list(pos.values())
    cx, cy = np.median(np.array(imc), axis=0)
    arvore = cKDTree(np.array(list(pos.values())))
    for n in itertools.count():
        r = FOLGA_ISOLADO * .35 * math.sqrt(n)
        p = (float(cx + r * math.cos(n * ANGULO_DOURADO)), float(cy + r * math.sin(n * ANGULO_DOURADO)))
        if arvore.query(p)[0] >= FOLGA_ISOLADO:
            return p


def _contorno(ref):
    """contorno da rede: distância máxima ao centro em cada direção.
    devolve (cx, cy, meia-largura, meia-altura, raios por setor)"""
    xs = [p[0] for p in ref.values()]
    ys = [p[1] for p in ref.values()]
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    hw, hh = (max(xs) - min(xs)) / 2 or 1, (max(ys) - min(ys)) / 2 or 1
    raio = [0.0] * SETORES
    for x, y in ref.values():
        u, v = (x - cx) / hw, (y - cy) / hh
        k = int((math.atan2(v, u) % (2 * math.pi)) / (2 * math.pi) * SETORES) % SETORES
        raio[k] = max(raio[k], math.hypot(u, v))
    # máximo móvel e depois média móvel pra arredondar
    cheio = [max(raio[(k + d) % SETORES] for d in range(-ALCANCE, ALCANCE + 1)) for k in range(SETORES)]
    liso = [sum(cheio[(k + d) % SETORES] for d in range(-SUAVIZAR, SUAVIZAR + 1)) / (2 * SUAVIZAR + 1)
            for k in range(SETORES)]
    return cx, cy, hw, hh, liso


def anel(nos, ref):
    """coloca os sem colaboração em anel em volta da rede, agrupados por instituto"""
    if not nos:
        return {}
    cx, cy, hw, hh, raio = _contorno(ref)
    unidade = (hw + hh) / 2                                   # mundo -> caixa normalizada
    ordem = sorted(nos, key=lambda k: (nos[k]['instituto'], nos[k]['label'], k))
    pos = {}
    for i, k in enumerate(ordem):
        ang = 2 * math.pi * i / len(ordem) - math.pi / 2      # começa no topo
        setor = int((ang % (2 * math.pi)) / (2 * math.pi) * SETORES) % SETORES
        r = raio[setor] + (FOLGA + i % VOLTAS * ENTRE_VOLTAS) / unidade
        pos[k] = (cx + r * hw * math.cos(ang), cy + r * hh * math.sin(ang))
    return pos
