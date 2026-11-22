# lê os CSVs e monta o grafo uma vez só (cache)
# 'sem colaboração' = pesquisadores da UNIFEI sem relação com o IMC, só vértices
from dataclasses import dataclass
from functools import lru_cache

from src.config import COR_GRUPO, DIMN, DIMS, PALETA
from src.engine import layout, loaders, peso
from src.schemas.graph_schema import (Atividade, AtividadeDetalhe, Edge, Graph, Node, NodeDetail, PesoParametros,
                                      Vizinho)


class NodeNotFound(Exception):
    pass


@dataclass(frozen=True)
class Universo:
    nos: dict
    arestas: dict
    grau: dict
    pos_livre: dict
    pos_area: dict

    def node(self, k: str) -> Node:
        v, p, q = self.nos[k], self.pos_livre[k], self.pos_area[k]
        return Node(id=k, label=v['label'], instituto=v['instituto'], area=v['area'], grupo=v['grupo'],
                    comp=v['comp'], mat=v['mat'], grau=self.grau.get(k, 0), lattes_url=v['lattes'],
                    x=round(p[0], 1), y=round(p[1], 1), x_area=round(q[0], 1), y_area=round(q[1], 1))

    def com_atividades(self) -> dict:
        """só relações com pelo menos uma atividade"""
        return {k: e for k, e in self.arestas.items() if sum(e['vc']) >= 1}


def _edge(k: tuple, e: dict, maiores: list[int]) -> Edge:
    return Edge(source=k[0], target=k[1], tipo_relacao=e['tipo'], vetor_contagem=e['vc'], vetor_bruto=e['vb'],
                soma_bruta=sum(e['vc']), peso=round(peso.peso_da_relacao(e['vc'], maiores), 6))


def _resposta(principal: Universo, sem_colab: Universo, atividades: dict, maiores: list[int]) -> Graph:
    ed = principal.com_atividades()
    com_aresta = {x for k in ed for x in k}
    nos = [k for k, v in principal.nos.items() if k in com_aresta or v['instituto'] == 'IMC']
    refs = {i for e in ed.values() for ids in e['vb'] for i in ids}
    return Graph(nodes=[principal.node(k) for k in nos], edges=[_edge(k, e, maiores) for k, e in ed.items()],
                 sem_colaboracao=[sem_colab.node(k) for k in sem_colab.nos],
                 atividades={i: Atividade(**atividades[i]) for i in refs if i in atividades},
                 paleta=PALETA, cores_grupo=COR_GRUPO, dimensoes=DIMN,
                 peso=PesoParametros(alfas=peso.alfas_em_ordem(), referencias=maiores))


@dataclass
class Engine:
    principal: Universo
    sem_colab: Universo
    atividades: dict
    maiores: list[int]      # maior contagem de cada dimensão
    resposta: Graph

    def graph(self) -> Graph:
        return self.resposta

    def detail(self, k: str) -> NodeDetail:
        u = self.principal if k in self.principal.nos else self.sem_colab if k in self.sem_colab.nos else None
        if u is None:
            raise NodeNotFound(k)
        viz = []
        for (a, b), e in u.arestas.items():
            if k not in (a, b):
                continue
            o = b if a == k else a
            acts = [AtividadeDetalhe(id=i, dimensao=DIMS[j],
                                     **self.atividades.get(i, {'ano': '', 'titulo': '(não encontrada)'}))
                    for j, ids in enumerate(e['vb']) for i in ids]
            viz.append(Vizinho(id=o, label=u.nos[o]['label'], instituto=u.nos[o]['instituto'], tipo_relacao=e['tipo'],
                               soma_bruta=sum(e['vc']), peso=round(peso.peso_da_relacao(e['vc'], self.maiores), 6),
                               vetor_contagem=e['vc'], atividades=acts))
        viz.sort(key=lambda v: -v.soma_bruta)
        return NodeDetail(**u.node(k).model_dump(), vizinhos=viz)


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    d = loaders.carregar()
    urls = loaders.lattes(d['unifei'])

    nos = loaders.vertices(d['entrada'], urls)
    arestas = loaders.arestas(d['saida'], nos)
    G = loaders.grafo(nos, arestas)
    principal = Universo(nos, arestas, dict(G.degree()), layout.livre(nos, G), layout.por_area(nos, G))

    extra = loaders.sem_colaboracao(d['unifei'], nos, d['saida'], urls)
    sem_colab = Universo(extra, {}, {}, layout.anel(extra, principal.pos_livre), layout.anel(extra, principal.pos_area))

    acts = loaders.atividades(d['atividades'])
    maiores = peso.referencias(principal.com_atividades())  # base comum pra todas as relações
    return Engine(principal, sem_colab, acts, maiores, _resposta(principal, sem_colab, acts, maiores))
