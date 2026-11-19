"""Layouts pré-calculados: livre (por conexões), separado por área (IMC ancorado) e o anel em volta
da rede, onde ficam os pesquisadores sem colaboração com o IMC."""
import itertools
import math

import networkx as nx
import numpy as np
from scipy.spatial import cKDTree

SC = 2000
CENTROS = {'Computação': (-.8, 0), 'Matemática': (.8, 0), 'Ambas': (0, 0), 'Outras': (0, -.9), 'Sem área': (0, -.9)}

# Distância ideal entre nós no spring_layout (quanto maior, mais espalhado). Cada layout tem o seu:
K_LIVRE = .8   # livre: abre os leques de externos e o miolo, sem deixar a rede crescer para fora
K_AREA = .18   # por área: os nós do IMC ficam fixos, e um k alto faria o resto explodir em volta deles

# Espaçamento entre nós (unidades do mundo). A distância mínima é a mesma que a física do frontend tenta
# manter (raio de colisão 4 × 5 = 20 por nó), para que o desenho do backend e a física não briguem.
DISTANCIA_MINIMA = 40
PASSOS_AFASTAR = 400                   # limite de rodadas do afastamento
FRACAO_DO_EMPURRAO = .6                # parte do empurrão aplicada por rodada (menor que 1 evita oscilar)
FOLGA_ISOLADO = 2 * DISTANCIA_MINIMA   # espaço livre em volta de quem não tem nenhuma relação
ANGULO_DOURADO = math.pi * (3 - math.sqrt(5))  # espalha pontos em espiral sem repetir direção

# Anel dos pesquisadores sem colaboração com o IMC (unidades do mundo; a rede principal ocupa ~2·SC × 2·SC).
FOLGA = 140         # entre o contorno da rede principal e a primeira volta do anel
VOLTAS = 3          # voltas concêntricas: espalha os pontos e evita que fiquem encostados
ENTRE_VOLTAS = 90   # distância entre voltas
SETORES = 180       # resolução angular com que o contorno da rede principal é medido
ALCANCE = 12        # setores vizinhos que o contorno cobre (máximo móvel); evita reentrâncias
SUAVIZAR = 9        # setores vizinhos na média que arredonda o contorno (sempre < ALCANCE)


def _spring(G, k, **kw):
    """Roda o spring_layout com os parâmetros comuns e escala para a tela."""
    p = nx.spring_layout(G, k=k, iterations=300, seed=7, **kw)
    return {n: (float(v[0]) * SC, float(v[1]) * SC) for n, v in p.items()}


def livre(nos, G):
    """Layout geral baseado nas conexões. Quem não tem nenhuma relação fica perto dos pesquisadores do IMC."""
    # O spring_layout empurra para a borda quem não tem arestas (nada o puxa de volta), e isso deformava o
    # anel. Por isso ele roda só com quem tem relações; os isolados são encaixados depois.
    ligados = G.subgraph([k for k in G if G.degree(k) > 0])
    pos = _afastar(_spring(ligados, K_LIVRE), set())
    for k in G:
        if G.degree(k) == 0:
            pos[k] = _perto_do_imc(nos, pos)
    return pos


def por_area(nos, G):
    """Posições iniciais por área do IMC (fixas) e layout para os demais."""
    # Grupos com o mesmo centro ('Outras' e 'Sem área') dividem um só círculo: antes cada um fazia o
    # seu, nos mesmos ângulos, e os professores dos dois grupos eram desenhados um em cima do outro.
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
    """Afasta os pares de nós mais próximos que DISTANCIA_MINIMA, até ninguém ficar grudado.

    A cada rodada, cada par perto demais é empurrado em sentidos opostos pela metade do que falta.
    Nós em `fixos` não se mexem. Determinístico: pontos coincidentes se separam numa direção que
    depende só da posição deles na lista.
    """
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
    """Primeiro lugar livre (ninguém a menos de FOLGA_ISOLADO) numa espiral a partir do centro do IMC."""
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
    """Contorno da rede principal: distância máxima ao centro em cada direção, já suavizada.

    Medido numa caixa normalizada (elipse unitária), para o anel acompanhar a proporção da tela.
    Devolve (cx, cy, meia-largura, meia-altura, raios por setor).
    """
    xs = [p[0] for p in ref.values()]
    ys = [p[1] for p in ref.values()]
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    hw, hh = (max(xs) - min(xs)) / 2 or 1, (max(ys) - min(ys)) / 2 or 1
    raio = [0.0] * SETORES
    for x, y in ref.values():
        u, v = (x - cx) / hw, (y - cy) / hh
        k = int((math.atan2(v, u) % (2 * math.pi)) / (2 * math.pi) * SETORES) % SETORES
        raio[k] = max(raio[k], math.hypot(u, v))
    # Máximo móvel (cobre buracos e pontas isoladas) e depois média móvel (arredonda). Como a média usa uma
    # janela menor que a do máximo, o resultado nunca fica abaixo da rede em nenhuma direção.
    cheio = [max(raio[(k + d) % SETORES] for d in range(-ALCANCE, ALCANCE + 1)) for k in range(SETORES)]
    liso = [sum(cheio[(k + d) % SETORES] for d in range(-SUAVIZAR, SUAVIZAR + 1)) / (2 * SUAVIZAR + 1)
            for k in range(SETORES)]
    return cx, cy, hw, hh, liso


def anel(nos, ref):
    """Posiciona os pesquisadores sem colaboração com o IMC em volta da rede principal (`ref`).

    São só pontos, sem relações entre eles. Ficam em voltas concêntricas que acompanham o contorno da
    rede principal, agrupados por instituto (cada instituto ocupa um arco contínuo). Nunca tocam nas
    posições da rede principal. Determinístico: as mesmas entradas produzem as mesmas posições.
    """
    if not nos:
        return {}
    cx, cy, hw, hh, raio = _contorno(ref)
    unidade = (hw + hh) / 2                                   # converte distâncias do mundo para a caixa normalizada
    ordem = sorted(nos, key=lambda k: (nos[k]['instituto'], nos[k]['label'], k))
    pos = {}
    for i, k in enumerate(ordem):
        ang = 2 * math.pi * i / len(ordem) - math.pi / 2      # começa no topo e segue no sentido horário
        setor = int((ang % (2 * math.pi)) / (2 * math.pi) * SETORES) % SETORES
        r = raio[setor] + (FOLGA + i % VOLTAS * ENTRE_VOLTAS) / unidade
        pos[k] = (cx + r * hw * math.cos(ang), cy + r * hh * math.sin(ang))
    return pos
