"""Leitura dos 4 CSVs e construção de vértices e arestas (estruturas simples em dict)."""
import json
import pandas as pd
from src.config import RAW, FILES, DIMS
from src.engine.areas import classificar

def _txt(x):
    """Converte valores não textuais em texto vazio.

    Entrada: valor isolado de uma célula do CSV.
    Saída: string original ou string vazia.
    """
    return x if isinstance(x, str) else ''

def carregar():
    """Carrega os quatro CSVs brutos em DataFrames.

    Entrada: nenhum argumento; usa os caminhos de src.config.
    Saída: dict com chaves saida, entrada, unifei e atividades.
    """
    return {k: pd.read_csv(RAW / f, dtype=str, low_memory=False) for k, f in FILES.items()}

def vertices(entrada, unifei):
    """Cria um nó por pesquisador com produção, área e URL do Lattes.

    Entrada: DataFrame de entrada e DataFrame da UNIFEI.
    Saída: dict pesquisador_id -> atributos do nó.
    """
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
    """Cria uma aresta não direcionada por par de pesquisadores.

    Entrada: DataFrame de relações e dict de nós.
    Saída: dict (id_a, id_b) -> atributos da aresta.
    """
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
