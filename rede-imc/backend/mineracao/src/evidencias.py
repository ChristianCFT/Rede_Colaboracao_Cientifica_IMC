# comparações entre registros usadas na deduplicação
import re
from difflib import SequenceMatcher

from src.textos import normalizar

ROMANOS = {'I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X'}
SO_DIGITOS = re.compile(r'\d+')


def semelhanca(titulo_a, titulo_b):
    """0 = nada em comum, 1 = iguais"""
    return SequenceMatcher(None, titulo_a, titulo_b).ratio()


def semelhanca_ou_vazio(a, b):
    """título vazio conta como igual"""
    if not a['titulo_normalizado'] or not b['titulo_normalizado']:
        return 1.0
    return semelhanca(a['titulo_normalizado'], b['titulo_normalizado'])


def dois_diferentes(a, b, campo):
    """ex: dois DOIs diferentes"""
    return bool(a[campo] and b[campo] and a[campo] != b[campo])


def ids_participantes(item):
    return {participante['id'] for participante in item['participantes']}


def ligados(a, b):
    return a['dono'] in ids_participantes(b) or b['dono'] in ids_participantes(a)


def evidencia_de_participantes(a, b):
    if ligados(a, b) or ids_participantes(a) & ids_participantes(b):
        return True
    return bool(nomes_normalizados(a) & nomes_normalizados(b))


def nomes_normalizados(item):
    nomes = set()
    for nome in item['nomes_lidos']:
        if normalizar(nome):
            nomes.add(normalizar(nome))
    return nomes


def membros(item):
    """ids identificados + nomes não resolvidos"""
    pessoas = ids_participantes(item)
    for nao_resolvido in item['nao_resolvidos']:
        pessoas.add(normalizar(nao_resolvido['nome']))
    return pessoas


def numeros_do_titulo(titulo):
    """números e romanos ('PARTE II')"""
    numeros = []
    for palavra in titulo.split():
        if SO_DIGITOS.fullmatch(palavra) or palavra in ROMANOS:
            numeros.append(palavra)
    return numeros
