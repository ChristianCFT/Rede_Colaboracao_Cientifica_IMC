"""Leitura dos 4 CSVs e construção de vértices, arestas, atividades e do grafo NetworkX."""
import json
from collections import defaultdict

import networkx as nx
import pandas as pd

from src.config import COLUNAS_ATIVIDADES, DIMS, FILES, RAW
from src.engine.areas import classificar


def _txt(x) -> str:
    """Converte valores não textuais (células vazias) em texto vazio."""
    return x if isinstance(x, str) else ''


def carregar() -> dict[str, pd.DataFrame]:
    """Carrega os quatro CSVs brutos (chaves: saida, entrada, unifei, atividades)."""
    usecols = dict(atividades=COLUNAS_ATIVIDADES)
    return {k: pd.read_csv(RAW / f, dtype=str, low_memory=False, usecols=usecols.get(k)) for k, f in FILES.items()}


def lattes(unifei: pd.DataFrame) -> dict[str, str]:
    """Mapa pesquisador_id -> URL do currículo Lattes."""
    return unifei.set_index('pesquisador_id')['lattes_url'].to_dict()


def vertices(entrada: pd.DataFrame, urls: dict[str, str]) -> dict[str, dict]:
    """Rede principal: um nó por pesquisador de dataset_entrada_IMC, com produção, área e URL do Lattes."""
    nos = {}
    for r in entrada.to_dict('records'):
        v = json.loads(r['vetor contagem']) if isinstance(r['vetor contagem'], str) else None
        area = _txt(r['area de trabalho'])
        no = dict(label=r['nome do pesquisador'], instituto=r['instituto'], area=area, obs=_txt(r['observacao']),
                  lattes=_txt(urls.get(r['pesquisador_id'])), prod=dict(zip(DIMS, map(int, v))) if v else None,
                  comp=False, mat=False, grupo='')
        if r['instituto'] == 'IMC':
            no.update(classificar(area))
        nos[r['pesquisador_id']] = no
    return nos


def arestas(saida: pd.DataFrame, nos: dict) -> dict[tuple[str, str], dict]:
    """Rede principal: uma aresta não direcionada por par de pesquisadores (vale a primeira linha do par)."""
    out = {}
    for r in saida.to_dict('records'):
        a, b = r['id pesquisador 1'], r['id pesquisador 2']
        k = tuple(sorted((a, b)))
        if k in out or a not in nos or b not in nos:
            continue
        out[k] = dict(tipo=r['tipo de relacao'], vc=json.loads(r['vetor contagem']), vb=json.loads(r['vetor bruto']))
    return out


def atividades(df: pd.DataFrame) -> dict[str, dict]:
    """Indexa as atividades (artigo, projeto, orientação...) pelo ID: id -> {ano, titulo}."""
    return {r.id_atividade: dict(ano=_txt(r.ano)[:4], titulo=_txt(r.titulo) or '(sem título)')
            for r in df.itertuples()}


def participacoes(df: pd.DataFrame) -> list[tuple[str, int, list[str]]]:
    """(id da atividade, dimensão 0..4, ids dos participantes) de cada atividade com participantes."""
    out = []
    for r in df.itertuples():
        if isinstance(r.ids_participantes, str) and isinstance(r.dimensao, str) and r.dimensao.lower() in DIMS:
            out.append((r.id_atividade, DIMS.index(r.dimensao.lower()), sorted(set(r.ids_participantes.split(';')))))
    return out


# ---- Pesquisadores sem colaboração com o IMC ----
# São só vértices: nenhuma relação entre eles é calculada nem exibida. O 'vetor contagem' de um
# pesquisador é o total de atividades de dataset_atividades_IMC (por dimensão) em que ele participa.

def sem_colaboracao(unifei: pd.DataFrame, principal: dict, saida: pd.DataFrame, urls: dict[str, str],
                    part: list) -> dict[str, dict]:
    """Pesquisadores de dataset_completo_UNIFEI fora da rede principal e sem relação direta com o IMC.

    O vínculo com o IMC vem do campo instituto; a colaboração, das relações de dataset_saida_IMC.
    """
    imc = {k for k, v in principal.items() if v['instituto'] == 'IMC'}
    imc |= set(unifei.loc[unifei['instituto'] == 'IMC', 'pesquisador_id'])
    colaboram = {b for a, b in zip(saida['id pesquisador 1'], saida['id pesquisador 2']) if a in imc}
    colaboram |= {a for a, b in zip(saida['id pesquisador 1'], saida['id pesquisador 2']) if b in imc}
    fora = unifei.dropna(subset=['pesquisador_id', 'nome', 'instituto']).drop_duplicates('pesquisador_id')
    fora = fora[~fora['pesquisador_id'].isin(principal.keys() | imc | colaboram)]

    contagem = defaultdict(lambda: [0] * len(DIMS))
    ids = set(fora['pesquisador_id'])
    for _, j, ps in part:
        for p in ps:
            if p in ids:
                contagem[p][j] += 1
    return {r['pesquisador_id']: dict(label=r['nome'], instituto=r['instituto'], area=_txt(r['area']), obs='',
                                      lattes=_txt(urls.get(r['pesquisador_id'])),
                                      prod=dict(zip(DIMS, contagem[r['pesquisador_id']]))
                                      if r['pesquisador_id'] in contagem else None,
                                      comp=False, mat=False, grupo='')
            for r in fora.to_dict('records')}


def grafo(nos: dict, arestas: dict) -> nx.Graph:
    """Constrói o grafo NetworkX usado pelos graus e pelos layouts."""
    G = nx.Graph()
    G.add_nodes_from(nos)
    G.add_edges_from(arestas)
    return G
