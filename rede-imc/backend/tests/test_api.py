"""Verificações mínimas dos dois endpoints usados pelo frontend (executar com os CSVs reais em data/raw)."""
import numpy as np
import pytest
from fastapi.testclient import TestClient

from src.main import app


@pytest.fixture(scope='module')
def c():
    with TestClient(app) as client:
        yield client


@pytest.fixture(scope='module')
def g(c):
    return c.get('/api/v1/graph').json()


def test_rede_principal_preservada(g):
    """Números da rede original do IMC (dados reais de data/raw)."""
    assert (len(g['nodes']), len(g['edges'])) == (1534, 2970)
    assert sum(n['comp'] for n in g['nodes'] if n['instituto'] == 'IMC') == 16
    assert len(g['sem_colaboracao']) == 284


def test_integridade(g):
    ids = {n['id'] for n in g['nodes']}
    assert len(ids) == len(g['nodes'])
    assert all(e['source'] in ids and e['target'] in ids and e['source'] != e['target'] for e in g['edges'])
    assert all(len(e['vetor_contagem']) == 5 and e['soma_bruta'] >= 1 for e in g['edges'])
    refs = {i for e in g['edges'] for d in e['vetor_bruto'] for i in d}
    assert set(g['atividades']) <= refs


def test_sem_colaboracao(g):
    """Só vértices: fora do IMC, fora da rede principal, sem relações e posicionados fora dela."""
    principal = {n['id']: n for n in g['nodes']}
    extra = g['sem_colaboracao']
    assert not principal.keys() & {n['id'] for n in extra}
    assert all(n['instituto'] != 'IMC' and n['grau'] == 0 for n in extra)
    # Nenhum ponto invade a rede principal: folga mínima em relação ao nó mais próximo.
    main_xy = np.array([(n['x'], n['y']) for n in g['nodes']])
    menor = min(np.hypot(*(main_xy - (n['x'], n['y'])).T).min() for n in extra)
    assert menor > 100


def test_detalhes_e_404(c, g):
    for nid in [g['nodes'][0]['id']] + [n['id'] for n in g['sem_colaboracao'][:1]]:
        d = c.get(f'/api/v1/nodes/{nid}').json()
        assert d['id'] == nid and d['vizinhos'] == sorted(d['vizinhos'], key=lambda v: -v['soma_bruta'])
    assert c.get(f"/api/v1/nodes/{g['sem_colaboracao'][0]['id']}").json()['vizinhos'] == []
    assert c.get('/api/v1/nodes/nao-existe').status_code == 404


@pytest.mark.parametrize('rota', ['/health', '/api/v1/graph/filter', '/api/v1/export/gexf'])
def test_rotas_removidas(c, rota):
    assert c.get(rota).status_code == 404
