"""Exporta GEXF (Gephi), GraphML (Cytoscape/yEd) e o pacote de dados do site."""
import json, math
import networkx as nx
from pathlib import Path
from src.config import DIMS, PALETA, COR_GRUPO

def _rgb(h):
    """Converte uma cor hexadecimal em componentes RGB.

    Entrada: cor hexadecimal iniciada por #.
    Saída: dict com chaves r, g e b.
    """
    return {c: int(h[i:i + 2], 16) for c, i in zip('rgb', (1, 3, 5))}

def construir(nos, arestas, pos, grau, viz):
    """Monta o grafo NetworkX com atributos próprios dos formatos de exportação.

    Entrada: nós, arestas, posições, graus e indicador de atributos visuais.
    Saída: instância nx.Graph pronta para exportação.
    """
    g = nx.Graph()
    for k, v in nos.items():
        at = dict(label=v['label'], instituto=v['instituto'], area_de_trabalho=v['area'], observacao=v['obs'],
                  lattes_url=v['lattes'], grau=grau.get(k, 0), grupo_imc=v['grupo'],
                  computacao=int(v['comp']), matematica=int(v['mat']))
        at.update({f'prod_{d}': n for d, n in (v['prod'] or {}).items()})
        if viz:
            cor = COR_GRUPO[v['grupo']] if v['instituto'] == 'IMC' else PALETA.get(v['instituto'], '#444444')
            at['viz'] = dict(color={**_rgb(cor), 'a': 1.0}, size=6 + 3 * math.sqrt(grau.get(k, 0)),
                             position=dict(x=pos[k][0], y=pos[k][1], z=0.0))
        else:
            at['pos_x'], at['pos_y'] = round(pos[k][0], 2), round(pos[k][1], 2)
        g.add_node(k, **at)
    for (a, b), e in arestas.items():
        g.add_edge(a, b, tipo_relacao=e['tipo'], escopo=e['escopo'], area_imc=e['area_imc'],
                   **dict(zip(DIMS, e['vc'])), soma_bruta=sum(e['vc']),
                   vetor_bruto=json.dumps(e['vb'], ensure_ascii=False))
    return g

def exportar(fmt: str, nos: dict, arestas: dict, pos: dict, grau: dict, destino: Path) -> Path:
    """Escreve o grafo em GEXF ou GraphML.

    Entrada: formato, nós, arestas, posições, graus e arquivo destino.
    Saída: caminho do arquivo criado.
    """
    if fmt == 'gexf':
        nx.write_gexf(construir(nos, arestas, pos, grau, True), destino)
    elif fmt == 'graphml':
        nx.write_graphml(construir(nos, arestas, pos, grau, False), destino)
    else:
        raise ValueError(fmt)
    return destino
