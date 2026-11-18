"""Orquestra pipeline + NetworkX uma única vez (cache) e serve os schemas da API."""
import collections
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
import networkx as nx
from src.config import CACHE, DIMS, DIMN, PALETA, COR_GRUPO
from src.schemas.graph_schema import (Area, Atividade, AtividadeDetalhe, Edge, Graph, GraphFilter, NetworkMetrics, Node,
                               NodeDetail, Producao, Vizinho)
from src.engine import exporters, layout, loaders

class NodeNotFound(Exception):
    pass

@dataclass
class Engine:
    nos: dict
    arestas: dict
    grau: dict
    pos_livre: dict
    pos_area: dict
    atividades: dict
    cen: dict
    inter: dict
    metricas: NetworkMetrics

    def node(self, k: str) -> Node:
        """Converte dados internos de um nó no schema Pydantic.

        Entrada: ID do pesquisador.
        Saída: objeto Node.
        """
        v, p, q = self.nos[k], self.pos_livre[k], self.pos_area[k]
        return Node(id=k, label=v['label'], instituto=v['instituto'], area=v['area'], grupo=v['grupo'], comp=v['comp'],
                    mat=v['mat'], grau=self.grau.get(k, 0), centralidade_grau=round(self.cen[k], 5),
                    intermediacao=round(self.inter[k], 5), lattes_url=v['lattes'], observacao=v['obs'],
                    producao=Producao(**v['prod']) if v['prod'] else None,
                    x=round(p[0], 1), y=round(p[1], 1), x_area=round(q[0], 1), y_area=round(q[1], 1))

    def edge(self, k: tuple, e: dict) -> Edge:
        """Converte dados internos de uma aresta no schema Pydantic.

        Entrada: tupla de IDs e atributos da aresta.
        Saída: objeto Edge.
        """
        return Edge(source=k[0], target=k[1], tipo_relacao=e['tipo'], escopo=e['escopo'], area_imc=e['area_imc'],
                    vetor_contagem=e['vc'], vetor_bruto=e['vb'], soma_bruta=sum(e['vc']))

    def _imc_ok(self, k: str, grupos: set[str] | None) -> bool:
        """Verifica se um nó atende ao filtro de grupos.

        Entrada: ID do nó e conjunto opcional de grupos.
        Saída: booleano indicando permanência no filtro.
        """
        v = self.nos[k]
        if v['instituto'] != 'IMC' or grupos is None:
            return True
        return (v['comp'] and 'Computação' in grupos) or (v['mat'] and 'Matemática' in grupos) or \
               (not v['comp'] and not v['mat'] and 'Outras' in grupos)

    def graph(self, f: GraphFilter | None = None) -> Graph:
        """Aplica filtros e monta o objeto completo do grafo.

        Entrada: filtros opcionais GraphFilter.
        Saída: objeto Graph com nós, arestas, áreas e métricas.
        """
        f = f or GraphFilter()
        gr = set(f.grupos) if f.grupos is not None else None
        ed = {k: e for k, e in self.arestas.items()
              if (not f.tipos or e['tipo'] in f.tipos) and sum(e['vc']) >= f.peso_min
              and self._imc_ok(k[0], gr) and self._imc_ok(k[1], gr)
              and (f.incluir_externos or 'EXT' not in e['tipo'])
              and (self.cen[k[0]] >= f.centralidade_min or self.cen[k[1]] >= f.centralidade_min)}
        com_aresta = {x for k in ed for x in k}
        keep = [k for k, v in self.nos.items() if k in com_aresta or (v['instituto'] == 'IMC' and self._imc_ok(k, gr))]
        refs = {i for e in ed.values() for d in e['vb'] for i in d}
        imc = [v for v in self.nos.values() if v['instituto'] == 'IMC']
        areas = [Area(nome=g, cor=COR_GRUPO[g], total=n) for g, n in (
            ('Computação', sum(v['comp'] for v in imc)), ('Matemática', sum(v['mat'] for v in imc)),
            ('Outras', sum(not v['comp'] and not v['mat'] for v in imc)))]
        return Graph(nodes=[self.node(k) for k in keep], edges=[self.edge(k, e) for k, e in ed.items()],
                     atividades={i: Atividade(**self.atividades[i]) for i in refs if i in self.atividades},
                     areas=areas, paleta=PALETA, cores_grupo=COR_GRUPO, dimensoes=DIMN, metricas=self.metricas)

    def detail(self, k: str) -> NodeDetail:
        """Busca um nó e monta seus vizinhos e atividades.

        Entrada: ID do pesquisador.
        Saída: objeto NodeDetail ou exceção NodeNotFound.
        """
        if k not in self.nos:
            raise NodeNotFound(k)
        viz = []
        for (a, b), e in self.arestas.items():
            if k not in (a, b):
                continue
            o = b if a == k else a
            acts = [AtividadeDetalhe(id=i, dimensao=DIMS[j], **self.atividades.get(i, {'ano': '', 'titulo': '(não encontrada)'}))
                    for j, ids in enumerate(e['vb']) for i in ids]
            viz.append(Vizinho(id=o, label=self.nos[o]['label'], instituto=self.nos[o]['instituto'], tipo_relacao=e['tipo'],
                               soma_bruta=sum(e['vc']), vetor_contagem=e['vc'], atividades=acts))
        viz.sort(key=lambda v: -v.soma_bruta)
        return NodeDetail(**self.node(k).model_dump(), vizinhos=viz)

    def export(self, fmt: str) -> Path:
        """Gera ou reutiliza o arquivo de exportação solicitado.

        Entrada: formato gexf ou graphml.
        Saída: caminho do arquivo exportado.
        """
        CACHE.mkdir(exist_ok=True)
        dest = CACHE / f'grafo_IMC.{fmt}'
        if not dest.exists():
            exporters.exportar(fmt, self.nos, self.arestas, self.pos_livre, self.grau, dest)
        return dest

@lru_cache(maxsize=1)
def get_engine() -> Engine:
    """Executa o pipeline pesado uma vez por processo.

    Entrada: nenhum argumento.
    Saída: Engine cacheado com grafo, layouts e métricas.
    """
    d = loaders.carregar()
    nos = loaders.vertices(d['entrada'], d['unifei'])
    arestas = loaders.arestas(d['saida'], nos)
    G = nx.Graph(); G.add_nodes_from(nos); G.add_edges_from(arestas)
    atv = {r.id_atividade: dict(ano=str(r.ano)[:4] if isinstance(r.ano, str) else '',
                                titulo=r.titulo if isinstance(r.titulo, str) else '(sem título)')
           for r in d['atividades'].itertuples()}
    m = NetworkMetrics(nos=G.number_of_nodes(), arestas=G.number_of_edges(), densidade=round(nx.density(G), 6),
                       grau_medio=round(2 * G.number_of_edges() / G.number_of_nodes(), 3),
                       componentes=nx.number_connected_components(G))
    return Engine(nos, arestas, dict(G.degree()), layout.livre(nos, arestas), layout.por_area(nos, arestas), atv,
                  nx.degree_centrality(G), nx.betweenness_centrality(G, k=300, seed=7), m)
