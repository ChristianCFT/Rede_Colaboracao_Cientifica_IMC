from src.engine.areas import classificar

def test_computacao():
    r = classificar('Ciências Exatas e da Terra / Ciência da Computação')
    assert (r['comp'], r['mat'], r['grupo']) == (True, False, 'Computação')

def test_matematica_e_estatistica():
    assert classificar('Ciências Exatas e da Terra / Matemática')['grupo'] == 'Matemática'
    assert classificar('Ciências Exatas e da Terra / Probabilidade e Estatística')['grupo'] == 'Matemática'

def test_varias_areas_entram_nos_dois_lados():
    r = classificar('Ciência da Computação; Matemática')
    assert (r['comp'], r['mat'], r['grupo']) == (True, True, 'Ambas')

def test_outras_e_sem_area():
    assert classificar('Ciências Exatas e da Terra / Física')['grupo'] == 'Outras'
    assert classificar('')['grupo'] == 'Sem área' and classificar(float('nan'))['grupo'] == 'Sem área'
