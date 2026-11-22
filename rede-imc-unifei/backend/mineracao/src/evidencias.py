"""Comparações entre dois registros usadas pelas regras de deduplicação.

Recebem dois itens brutos (ou dois títulos já normalizados) e devolvem um número ou um
sim/não: semelhança de título, DOI conflitante, participante em comum, mesmos membros.
"""
import re
from difflib import SequenceMatcher

from src.textos import normalizar

ROMANOS = {'I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X'}
# Captura uma palavra feita só de dígitos.
SO_DIGITOS = re.compile(r'\d+')


def semelhanca(titulo_a, titulo_b):
    """Recebe dois títulos normalizados e devolve a semelhança (0 = nada em comum, 1 = iguais)."""
    return SequenceMatcher(None, titulo_a, titulo_b).ratio()


def semelhanca_ou_vazio(a, b):
    """Como semelhanca, mas recebe dois itens; um título vazio conta como igual (1,0)."""
    if not a['titulo_normalizado'] or not b['titulo_normalizado']:
        return 1.0
    return semelhanca(a['titulo_normalizado'], b['titulo_normalizado'])


def dois_diferentes(a, b, campo):
    """Os dois itens têm o campo preenchido e com valores diferentes (ex.: dois DOIs)?"""
    return bool(a[campo] and b[campo] and a[campo] != b[campo])


def ids_participantes(item):
    """Recebe um item e devolve o conjunto de ids identificados nele."""
    return {participante['id'] for participante in item['participantes']}


def ligados(a, b):
    """O dono de um dos registros aparece identificado no outro?"""
    return a['dono'] in ids_participantes(b) or b['dono'] in ids_participantes(a)


def evidencia_de_participantes(a, b):
    """Ligados, ou um participante identificado em comum, ou o mesmo nome lido nos dois?"""
    if ligados(a, b) or ids_participantes(a) & ids_participantes(b):
        return True
    return bool(nomes_normalizados(a) & nomes_normalizados(b))


def nomes_normalizados(item):
    """Recebe um item e devolve os nomes lidos nele (identificados ou não), normalizados."""
    nomes = set()
    for nome in item['nomes_lidos']:
        if normalizar(nome):
            nomes.add(normalizar(nome))
    return nomes


def membros(item):
    """Recebe um item e devolve quem está nele: ids identificados + nomes não resolvidos."""
    pessoas = ids_participantes(item)
    for nao_resolvido in item['nao_resolvidos']:
        pessoas.add(normalizar(nao_resolvido['nome']))
    return pessoas


def numeros_do_titulo(titulo):
    """Recebe um título normalizado e devolve seus números e numerais romanos ('PARTE II')."""
    numeros = []
    for palavra in titulo.split():
        if SO_DIGITOS.fullmatch(palavra) or palavra in ROMANOS:
            numeros.append(palavra)
    return numeros
