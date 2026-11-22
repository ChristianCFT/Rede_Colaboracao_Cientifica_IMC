"""Etapa 4 (fim): transforma cada grupo de registros repetidos numa atividade única.

Recebe os grupos montados pela deduplicação (cada grupo em ordem de leitura, os grupos na ordem
do seu primeiro item) e devolve uma atividade por grupo, com todos os participantes e fontes.
"""
import collections

from src.textos import normalizar

# Motivos de nomes que nem chegam a ser pessoas e não vão para 'nomes_nao_resolvidos'.
MOTIVOS_DESCARTADOS = ('et al', 'vazio', 'nao_e_pessoa')


def consolidar(grupos):
    """Recebe a lista de grupos de itens e devolve a lista de atividades."""
    # Os ids dos externos já chegam resolvidos da etapa 3 (externos.py): aqui nada é juntado.
    atividades = []
    for grupo in grupos:
        atividades.append(montar_atividade(grupo))
    return atividades


def montar_atividade(grupo):
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
        'participantes': juntar_participantes(grupo),
        'nao_resolvidos': juntar_nao_resolvidos(grupo),
        'cvs': sorted({item['dono'] for item in grupo}),
        'fontes': [item['fonte'] for item in grupo],
        'quantidade_registros': len(grupo),
        'codigo': '',
    }
    atividade['chave'] = chave_de_deduplicacao(atividade)
    return atividade


def juntar_participantes(grupo):
    """Devolve {id: {'papeis', 'metodos'}} lendo os registros em ordem de fonte."""
    participantes = {}
    for item in sorted(grupo, key=ler_fonte):
        for participante in item['participantes']:
            pessoa = participante['id']
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
