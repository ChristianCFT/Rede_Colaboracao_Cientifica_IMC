import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture(scope='module')
def c():
    with TestClient(app) as client:
        yield client

def test_health(c):
    assert c.get('/health').json() == {'status': 'ok'}

def test_graph_completo(c):
    g = c.get('/api/v1/graph').json()
    assert (len(g['nodes']), len(g['edges'])) == (1486, 2828)
    assert g['metricas']['nos'] == 1486 and g['metricas']['componentes'] >= 1
    ids = {n['id'] for n in g['nodes']}
    assert all(e['source'] in ids and e['target'] in ids and e['source'] != e['target'] for e in g['edges'])
    assert all(len(e['vetor_contagem']) == 5 for e in g['edges'])
    assert {a['nome']: a['total'] for a in g['areas']}['Computação'] == 16

def test_filtro_por_area_e_peso(c):
    g = c.get('/api/v1/graph/filter', params={'grupos': ['Matemática'], 'peso_min': 2, 'incluir_externos': False}).json()
    assert 0 < len(g['edges']) < 2828
    assert all(e['soma_bruta'] >= 2 and 'EXT' not in e['tipo_relacao'] for e in g['edges'])
    assert all(n['mat'] for n in g['nodes'] if n['instituto'] == 'IMC')

def test_filtro_invalido(c):
    assert c.get('/api/v1/graph/filter', params={'peso_min': 0}).status_code == 422

def test_no_e_404(c):
    nid = c.get('/api/v1/graph').json()['nodes'][0]['id']
    d = c.get(f'/api/v1/nodes/{nid}').json()
    assert d['id'] == nid and d['vizinhos'] == sorted(d['vizinhos'], key=lambda v: -v['soma_bruta'])
    assert c.get('/api/v1/nodes/nao-existe').status_code == 404

@pytest.mark.parametrize('fmt', ['gexf', 'graphml'])
def test_export(c, fmt):
    r = c.get(f'/api/v1/export/{fmt}')
    assert r.status_code == 200 and r.content.startswith(b'<?xml')

def test_export_formato_invalido(c):
    assert c.get('/api/v1/export/pdf').status_code == 422
