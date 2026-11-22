import json

import networkx as nx
import pandas as pd

from src.config import COLUNAS_ATIVIDADES, FILES, RAW
from src.engine.areas import classificar


def _txt(x) -> str:
    return x if isinstance(x, str) else ''


def carregar() -> dict[str, pd.DataFrame]:
    usecols = dict(atividades=COLUNAS_ATIVIDADES)
    return {k: pd.read_csv(RAW / f, dtype=str, low_memory=False, usecols=usecols.get(k)) for k, f in FILES.items()}


def lattes(unifei: pd.DataFrame) -> dict[str, str]:
    return unifei.set_index('pesquisador_id')['lattes_url'].to_dict()


def vertices(entrada: pd.DataFrame, urls: dict[str, str]) -> dict[str, dict]:
    nos = {}
    for r in entrada.to_dict('records'):
        area = _txt(r['area de trabalho'])
        no = dict(label=r['nome do pesquisador'], instituto=r['instituto'], area=area,
                  lattes=_txt(urls.get(r['pesquisador_id'])), comp=False, mat=False, grupo='')
        if r['instituto'] == 'IMC':
            no.update(classificar(area))
        nos[r['pesquisador_id']] = no
    return nos


def arestas(saida: pd.DataFrame, nos: dict) -> dict[tuple[str, str], dict]:
    """uma aresta por par (vale a primeira linha)"""
    out = {}
    for r in saida.to_dict('records'):
        a, b = r['id pesquisador 1'], r['id pesquisador 2']
        k = tuple(sorted((a, b)))
        if k in out or a not in nos or b not in nos:
            continue
        out[k] = dict(tipo=r['tipo de relacao'], vc=json.loads(r['vetor contagem']), vb=json.loads(r['vetor bruto']))
    return out


def atividades(df: pd.DataFrame) -> dict[str, dict]:
    return {r.id_atividade: dict(ano=_txt(r.ano)[:4], titulo=_txt(r.titulo) or '(sem título)')
            for r in df.itertuples()}


# pesquisadores sem colaboração com o IMC (só vértices)

def sem_colaboracao(unifei: pd.DataFrame, principal: dict, saida: pd.DataFrame,
                    urls: dict[str, str]) -> dict[str, dict]:
    """pesquisadores da UNIFEI fora da rede e sem relação com o IMC"""
    imc = {k for k, v in principal.items() if v['instituto'] == 'IMC'}
    imc |= set(unifei.loc[unifei['instituto'] == 'IMC', 'pesquisador_id'])
    colaboram = {b for a, b in zip(saida['id pesquisador 1'], saida['id pesquisador 2']) if a in imc}
    colaboram |= {a for a, b in zip(saida['id pesquisador 1'], saida['id pesquisador 2']) if b in imc}
    fora = unifei.dropna(subset=['pesquisador_id', 'nome', 'instituto']).drop_duplicates('pesquisador_id')
    fora = fora[~fora['pesquisador_id'].isin(principal.keys() | imc | colaboram)]
    return {r['pesquisador_id']: dict(label=r['nome'], instituto=r['instituto'], area=_txt(r['area']),
                                      lattes=_txt(urls.get(r['pesquisador_id'])), comp=False, mat=False, grupo='')
            for r in fora.to_dict('records')}


def grafo(nos: dict, arestas: dict) -> nx.Graph:
    G = nx.Graph()
    G.add_nodes_from(nos)
    G.add_edges_from(arestas)
    return G
