"""Layouts pré-calculados: livre (por conexões), separado por área (IMC ancorado) e o anel em volta
da rede, onde ficam os pesquisadores sem colaboração com o IMC."""
import math

import networkx as nx

SC = 2000
CENTROS = {'Computação': (-.8, 0), 'Matemática': (.8, 0), 'Ambas': (0, 0), 'Outras': (0, -.9), 'Sem área': (0, -.9)}

# Distância ideal entre nós no spring_layout (quanto maior, mais espalhado). Cada layout tem o seu:
K_LIVRE = .8   # livre: abre os leques de externos e o miolo, sem deixar a rede crescer para fora
K_AREA = .18   # por área: os nós do IMC ficam fixos, e um k alto faria o resto explodir em volta deles

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


def livre(G):
    """Layout geral baseado nas conexões."""
    return _spring(G, K_LIVRE)


def por_area(nos, G):
    """Posições iniciais por área do IMC (fixas) e layout para os demais."""
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
    return _spring(G, K_AREA, pos=ini, fixed=list(ini))


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
