"""Leitura dos 4 CSVs e construção de vértices e arestas (estruturas simples em dict)."""
import json
import pandas as pd
from app.core.config import RAW, FILES, DIMS
from app.services.graph_engine.areas import classificar

def _txt(x):
    return x if isinstance(x, str) else ''

def carregar():
    return {k: pd.read_csv(RAW / f, dtype=str, low_memory=False) for k, f in FILES.items()}

def vertices(entrada, unifei):
    """Um nó por pesquisador_id (dataset de entrada) + lattes do dataset da UNIFEI."""
    lattes = unifei.set_index('pesquisador_id')['lattes_url'].to_dict()
    nos = {}
    for _, r in entrada.iterrows():
        v = json.loads(r['vetor contagem']) if isinstance(r['vetor contagem'], str) else None
        area = _txt(r['area de trabalho'])
        no = dict(label=r['nome do pesquisador'], instituto=r['instituto'], area=area, obs=_txt(r['observacao']),
                  lattes=_txt(lattes.get(r['pesquisador_id'])), prod=dict(zip(DIMS, map(int, v))) if v else None,
                  comp=False, mat=False, grupo='')
        if r['instituto'] == 'IMC':
            no.update(classificar(area))
        nos[r['pesquisador_id']] = no
    return nos

def arestas(saida, nos):
    """Uma aresta por par (não direcionado). IMC-IMC vem duplicado nos dois sentidos na fonte."""
    out = {}
    for _, r in saida.iterrows():
        a, b = r['id pesquisador 1'], r['id pesquisador 2']
        k = tuple(sorted((a, b)))
        if k in out:
            continue
        t = r['tipo de relacao']
        grupos = sorted(nos[x]['grupo'] for x in (a, b) if nos[x]['instituto'] == 'IMC')
        out[k] = dict(tipo=t, escopo='IMC interna' if t == 'IMC-IMC' else 'Externa (EXT)' if t == 'IMC-EXT'
                      else 'UNIFEI (outro instituto)', vc=json.loads(r['vetor contagem']),
                      vb=json.loads(r['vetor bruto']), area_imc='–'.join(grupos))
    return out
