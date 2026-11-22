"""Etapa 3: descobre quem é cada nome lido nos currículos (níveis 1 a 5).

Recebe os professores e as correspondências confirmadas à mão e monta o índice de busca;
resolver_nome devolve o id da pessoa (professor ou externo) ou o motivo de não identificar.
"""
import collections
import json
import re

from configuracao import ARQUIVO_CORRESPONDENCIAS, PALAVRAS_DE_INSTITUICAO
from src.textos import (PARTICULAS, PARTICULAS_MULTILETRA, forma_natural, hash_curto,
                        limpar_espacos, normalizar, normalizar_sem_particulas)

# O índice é um dicionário com as chaves:
#   nomes {nome normalizado ou '~' + nome sem partículas: id}   por_lattes {Lattes iD: id}
#   citacoes {chave de citação: id}   citacoes_ambiguas {chaves de mais de um professor}
#   confirmadas {chave de citação: id}   primeiro_e_ultimo {(primeiro nome, último nome)}
#   externos {id EXT: {'lattes': Lattes iD ou '', 'nomes': Counter dos nomes vistos}}

# Partículas ignoradas na chave de citação ('SILVA, J. DA' == 'SILVA, J.').
PARTICULAS_CITACAO = {'DE', 'DA', 'DO', 'DAS', 'DOS', 'DEL', 'DI', 'DU', 'VAN', 'VON', 'DER'}
# Abreviações de sufixo trocadas pela forma completa na chave de citação.
SUFIXO_COMPLETO = {'JR': 'JUNIOR', 'FO': 'FILHO', 'FHO': 'FILHO', 'NT': 'NETO'}
# Captura uma inicial abreviada com ponto ('J.' ou 'Jr.').
INICIAL_COM_PONTO = re.compile(r'\b[A-Za-zÀ-ÿ]{1,2}\.')
NOMES_VAZIOS = ('ET AL', 'ET AL I')


def ler_correspondencias():
    """Lê as identidades confirmadas à mão (citações e Lattes); sem o arquivo, nenhuma."""
    if not ARQUIVO_CORRESPONDENCIAS.exists():
        return {}
    with open(ARQUIVO_CORRESPONDENCIAS, encoding='utf-8') as arquivo:
        return json.load(arquivo)


def montar_indice(professores, confirmadas):
    """Recebe os professores e o JSON de correspondências e devolve o índice de busca."""
    ids = {professor['id'] for professor in professores}
    indice = {'externos': {}, 'confirmadas': {}, 'primeiro_e_ultimo': set(),
              'por_lattes': mapa_por_lattes(professores, confirmadas, ids),
              'nomes': mapa_por_nome(professores)}
    for confirmada in confirmadas.get('citacoes', []):
        if confirmada.get('pesquisador_id') in ids:
            indice['confirmadas'][chave_citacao(confirmada['forma'])] = confirmada['pesquisador_id']
    indice['citacoes'], indice['citacoes_ambiguas'] = mapas_por_citacao(professores)
    for professor in professores:
        palavras = normalizar_sem_particulas(professor['nome']).split()
        if len(palavras) >= 2:
            indice['primeiro_e_ultimo'].add((palavras[0], palavras[-1]))
    return indice


def mapa_por_lattes(professores, confirmadas, ids):
    """Devolve {Lattes iD: id do professor} só para Lattes que pertencem a um único professor."""
    donos = {}
    for professor in professores:
        if professor['lattes']:
            donos.setdefault(professor['lattes'], []).append(professor['id'])
    confirmados = {}
    for confirmada in confirmadas.get('lattes', []):
        if confirmada.get('pesquisador_id') in ids:
            confirmados[confirmada['lattes_id']] = confirmada['pesquisador_id']
    for lattes, professor in confirmados.items():
        lista = donos.setdefault(lattes, [])
        if professor not in lista:
            lista.append(professor)
    mapa = {}
    for lattes, lista in donos.items():
        if len(lista) == 1:
            mapa[lattes] = lista[0]
    return mapa


def mapa_por_nome(professores):
    """Devolve {nome normalizado: id}; um nome que pertence a dois professores fica de fora."""
    donos = {}
    for professor in professores:
        for nome in (professor['nome'], professor['pasta'], professor['nome_indice']):
            if nome:
                donos.setdefault(normalizar(nome), set()).add(professor['id'])
                donos.setdefault('~' + normalizar_sem_particulas(nome), set()).add(professor['id'])
    return {chave: min(ids) for chave, ids in donos.items() if len(ids) == 1}


def mapas_por_citacao(professores):
    """Devolve ({citação: id} das citações de um só professor, {citações de mais de um})."""
    donos = {}
    for professor in professores:
        for citacao in professor['citacoes']:
            if citacao_especifica(citacao):
                donos.setdefault(chave_citacao(citacao), set()).add(professor['id'])
    unicas, ambiguas = {}, set()
    for chave, ids in donos.items():
        if len(ids) == 1:
            unicas[chave] = min(ids)
        else:
            ambiguas.add(chave)
    return unicas, ambiguas


def chaves_do_dono(professor):
    """Devolve as formas pelas quais o dono do currículo aparece nos próprios itens."""
    chaves = {normalizar(professor['nome']), normalizar(forma_natural(professor['nome']))}
    for citacao in professor['citacoes']:
        chaves.add(normalizar(citacao))
        chaves.add(chave_citacao(citacao))
    return chaves


def resolver_nome(nome, links, dono, chaves_dono, indice, exigir_lattes=False, lattes_dono=''):
    """Recebe um nome lido num item e devolve (id ou None, método ou motivo)."""
    texto = limpar_espacos(nome).strip(' .;,')
    if len(texto) < 2:
        return None, 'vazio'
    normalizado = normalizar(texto)
    if normalizado in NOMES_VAZIOS:
        return None, 'et al'
    # Nível 1: o próprio item traz o link para o Lattes desse nome.
    lattes = links.get(normalizado)
    if lattes:
        if dono and lattes_dono and lattes == lattes_dono:
            return dono, 'dono_do_cv'
        return professor_ou_externo_por_lattes(lattes, texto, indice), 'lattes_id'
    # Nível 2: é o dono do currículo (citações declaradas ou nome em negrito).
    if dono and (normalizado in chaves_dono or chave_citacao(texto) in chaves_dono):
        return dono, 'dono_do_cv'
    encontrado = procurar_professor(texto, indice)
    if encontrado:
        return encontrado
    return classificar_desconhecido(texto, indice, exigir_lattes)


def procurar_professor(texto, indice):
    """Níveis 3 e 4: devolve (id, método) por nome completo ou citação única; senão None."""
    natural = forma_natural(texto)
    candidatos = (normalizar(natural), '~' + normalizar_sem_particulas(natural),
                  normalizar(texto), '~' + normalizar_sem_particulas(texto))
    for candidato in candidatos:
        if candidato in indice['nomes']:
            return indice['nomes'][candidato], 'nome_completo_professor'
    chave = chave_citacao(texto)
    if chave in indice['citacoes']:
        return indice['citacoes'][chave], 'citacao_declarada'
    palavras = texto.split()
    if ',' not in texto and len(palavras) >= 2:
        # 'Fulano Silva' pode ser a citação 'SILVA, Fulano' escrita na ordem natural.
        invertido = palavras[-1] + ', ' + ' '.join(palavras[:-1])
        if chave_citacao(invertido) in indice['citacoes'] and citacao_especifica(invertido):
            return indice['citacoes'][chave_citacao(invertido)], 'citacao_declarada'
    if chave in indice['confirmadas']:
        return indice['confirmadas'][chave], 'confirmado_manualmente'
    if chave in indice['citacoes_ambiguas']:
        return None, 'citacao_ambigua'
    return None


def classificar_desconhecido(texto, indice, exigir_lattes):
    """Nível 5: devolve (id EXT-N, método) para nome completo; senão (None, motivo)."""
    if eh_instituicao(texto):
        return None, 'nao_e_pessoa'
    natural = forma_natural(texto)
    palavras = [palavra for palavra in normalizar(natural).split() if palavra not in PARTICULAS]
    abreviado = esta_abreviado(texto)
    if len(palavras) >= 2 and not abreviado:
        if (palavras[0], palavras[-1]) in indice['primeiro_e_ultimo']:
            return None, 'possivel_professor'
    if abreviado:
        return None, 'abreviado'
    if exigir_lattes:
        return None, 'aluno_sem_lattes'
    if len(palavras) < 3:
        return None, 'nome_curto'
    return externo_por_nome(natural, indice), 'nome_completo_externo'


def eh_instituicao(texto):
    """O texto lido como nome é uma instituição ou um endereço ('UNIVERSIDADE FEDERAL DE ...')?"""
    return bool(set(normalizar(texto).split()) & PALAVRAS_DE_INSTITUICAO)


def professor_ou_externo_por_lattes(lattes, nome, indice):
    """Recebe um Lattes iD visto num link e devolve o id do professor ou do externo EXT-L."""
    if lattes in indice['por_lattes']:
        return indice['por_lattes'][lattes]
    return registrar_externo('EXT-L' + lattes, lattes, nome, indice)


def externo_por_nome(nome_natural, indice):
    """Recebe o nome completo de um externo sem link e devolve o id EXT-N (hash do nome)."""
    identificador = 'EXT-N' + hash_curto(normalizar_sem_particulas(nome_natural))
    return registrar_externo(identificador, '', nome_natural, indice)


def registrar_externo(identificador, lattes, nome, indice):
    """Guarda o externo no índice (se for novo), conta mais uma vez o nome e devolve o id."""
    if identificador not in indice['externos']:
        indice['externos'][identificador] = {'lattes': lattes, 'nomes': collections.Counter()}
    indice['externos'][identificador]['nomes'][limpar_espacos(nome)] += 1
    return identificador


def chave_citacao(citacao):
    """Recebe uma citação e devolve a chave normalizada, com 'JR' -> 'JUNIOR' e sem partículas."""
    palavras = []
    for palavra in normalizar(citacao).split():
        palavra = SUFIXO_COMPLETO.get(palavra, palavra)
        if palavra not in PARTICULAS_CITACAO:
            palavras.append(palavra)
    return ' '.join(palavras)


def citacao_especifica(citacao):
    """A citação identifica alguém? 'SILVA, J.' é genérica; 'SILVA, J. C.' não."""
    prenomes = citacao.split(',', 1)[1] if ',' in citacao else citacao
    palavras = []
    for palavra in normalizar(prenomes).split():
        if palavra not in PARTICULAS_MULTILETRA:
            palavras.append(palavra)
    if len(palavras) >= 2:
        return True
    return len(palavras) == 1 and len(palavras[0]) >= 3


def esta_abreviado(nome):
    """O nome tem alguma inicial solta ('J' ou 'J.')? Abreviação nunca vira identidade sozinha."""
    for palavra in normalizar(forma_natural(nome)).split():
        if palavra not in PARTICULAS and len(palavra) == 1:
            return True
    return INICIAL_COM_PONTO.search(nome) is not None
