# etapa 4: transforma cada grupo de registros repetidos numa atividade só
import collections

from src.textos import normalizar

# esses motivos nem são pessoas, não vão pra nomes_nao_resolvidos
MOTIVOS_DESCARTADOS = ('et al', 'vazio', 'nao_e_pessoa')


def consolidar(grupos):
    atividades = []
    for grupo in grupos:
        atividades.append(montar_atividade(grupo))
    return atividades


def montar_atividade(grupo):
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
    return item['fonte']


def juntar_nao_resolvidos(grupo):
    """um por nome normalizado (vale o primeiro)"""
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
    """valor mais frequente (empate: mais longo, depois alfabético)"""
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
    """DOI, número de registro ou 'dimensão|tipo|pessoa|título|ano'"""
    if atividade['dim'] == 'ART' and atividade['doi']:
        return 'DOI:' + atividade['doi']
    if atividade['dim'] == 'PTT' and atividade['registro']:
        return 'REG:' + atividade['registro']
    partes = [atividade['dim'], atividade['subtipo'], normalizar(atividade['aluno_ou_candidato']),
              normalizar(atividade['titulo']), atividade['ano']]
    return '|'.join(partes)
