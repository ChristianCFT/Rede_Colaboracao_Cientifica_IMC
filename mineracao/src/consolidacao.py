"""Etapa 4 (fim): transforma cada grupo de registros repetidos numa atividade única.

Recebe os grupos montados pela deduplicação (cada grupo em ordem de leitura, os grupos na ordem
do seu primeiro item) e devolve uma atividade por grupo, com todos os participantes e fontes.
"""
import collections
import re

from src.textos import normalizar, normalizar_sem_particulas

# Captura 'SOBRENOME, Nomes' para reescrever como 'Nomes SOBRENOME'.
NOME_INVERTIDO = re.compile(r'^(.*?),\s*(.*)$')
# Motivos de nomes que nem chegam a ser pessoas e não vão para 'nomes_nao_resolvidos'.
MOTIVOS_DESCARTADOS = ('et al', 'vazio')


def consolidar(grupos):
    """Recebe a lista de grupos de itens e devolve a lista de atividades."""
    apelidos = {}
    for grupo in grupos:
        juntar_apelidos(grupo, apelidos)
    atividades = []
    for grupo in grupos:
        atividades.append(montar_atividade(grupo, apelidos))
    return atividades


def juntar_apelidos(grupo, apelidos):
    """Acrescenta aos apelidos os EXT-N que, no mesmo grupo, aparecem também como EXT-L."""
    # O mesmo externo pode vir com link (EXT-L) num CV e sem link (EXT-N) em outro: quando isso
    # acontece na mesma atividade, com o mesmo nome, o EXT-N passa a ser o EXT-L.
    com_link = {}
    for item in grupo:
        for participante in item['participantes']:
            if participante['id'].startswith('EXT-L'):
                com_link[nome_natural(participante['nome'])] = participante['id']
    for item in grupo:
        for participante in item['participantes']:
            if not participante['id'].startswith('EXT-N'):
                continue
            chave = nome_natural(participante['nome'])
            if chave in com_link:
                apelidos[participante['id']] = com_link[chave]


def nome_natural(nome):
    """'SILVA, Ana Maria' -> 'ANA MARIA SILVA' (normalizado e sem partículas)."""
    return normalizar_sem_particulas(NOME_INVERTIDO.sub(r'\2 \1', nome))


def montar_atividade(grupo, apelidos):
    """Recebe os registros de uma mesma atividade e devolve a atividade consolidada."""
    atividade = {
        'dim': grupo[0]['dim'],
        'subtipo': ' / '.join(sorted({item['subtipo'] for item in grupo})),
        'titulo': mais_comum([item['titulo'] for item in grupo]),
        'ano': mais_comum([item['ano'] for item in grupo]),
        'doi': mais_comum([item['doi'] for item in grupo]),
        'registro': mais_comum([item['registro'] for item in grupo]),
        'aluno_ou_candidato': mais_comum([item['aluno'] or item['candidato'] for item in grupo]),
        'periodo': mais_comum([item['periodo'] for item in grupo]),
        'situacao': mais_comum([item['situacao'] for item in grupo]),
        'participantes': juntar_participantes(grupo, apelidos),
        'nao_resolvidos': juntar_nao_resolvidos(grupo),
        'cvs': sorted({item['dono'] for item in grupo}),
        'fontes': [item['fonte'] for item in grupo],
        'quantidade_registros': len(grupo),
        'codigo': '',
    }
    atividade['chave'] = chave_de_deduplicacao(atividade)
    return atividade


def juntar_participantes(grupo, apelidos):
    """Devolve {id: {'papeis', 'metodos'}} lendo os registros em ordem de fonte."""
    participantes = {}
    for item in sorted(grupo, key=ler_fonte):
        for participante in item['participantes']:
            pessoa = apelidos.get(participante['id'], participante['id'])
            if pessoa not in participantes:
                participantes[pessoa] = {'papeis': set(), 'metodos': set()}
            participantes[pessoa]['papeis'].add(participante['papel'])
            participantes[pessoa]['metodos'].add(participante['metodo'])
    return participantes


def ler_fonte(item):
    """Chave de ordenação dos registros de uma atividade: a fonte ('dono|subtipo|item n')."""
    return item['fonte']


def juntar_nao_resolvidos(grupo):
    """Devolve os nomes sem identidade, um por nome normalizado (o primeiro visto vale)."""
    por_nome = {}
    for item in grupo:
        for nao_resolvido in item['nao_resolvidos']:
            por_nome.setdefault(normalizar(nao_resolvido['nome']), nao_resolvido)
    lista = []
    for nao_resolvido in por_nome.values():
        if nao_resolvido['motivo'] not in MOTIVOS_DESCARTADOS:
            lista.append(nao_resolvido)
    return lista


def mais_comum(valores):
    """Devolve o valor não vazio mais frequente (empate: o mais longo, depois o alfabético)."""
    contagem = collections.Counter(valor for valor in valores if valor)
    if not contagem:
        return ''
    maior = max(contagem.values())
    escolhido = None
    for valor, vezes in contagem.items():
        if vezes != maior:
            continue
        if escolhido is None or (-len(valor), valor) < (-len(escolhido), escolhido):
            escolhido = valor
    return escolhido


def chave_de_deduplicacao(atividade):
    """DOI (artigo), número de registro (PTT) ou 'dimensão|tipo|pessoa|título|ano'."""
    if atividade['dim'] == 'ART' and atividade['doi']:
        return 'DOI:' + atividade['doi']
    if atividade['dim'] == 'PTT' and atividade['registro']:
        return 'REG:' + atividade['registro']
    partes = [atividade['dim'], atividade['subtipo'], normalizar(atividade['aluno_ou_candidato']),
              normalizar(atividade['titulo']), atividade['ano']]
    return '|'.join(partes)
