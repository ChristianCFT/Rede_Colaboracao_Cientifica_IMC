"""Etapa 5: monta a rede da camada (IMC): pares de pesquisadores, códigos das atividades e vetores.

Recebe as atividades únicas e os professores; devolve a rede (dicionário descrito abaixo) com
as atividades do dataset já numeradas (ART-000001, PRJ-000001, ...).
"""
from configuracao import (CAMADA, DIMENSOES, PALAVRA_DE_CANDIDATO, PAPEIS_DE_SUPERVISAO,
                          PAPEL_DE_MEMBRO_DE_BANCA, PAPEL_DE_ORIENTANDO)
from src.textos import normalizar

# A rede é um dicionário com as chaves:
#   membros       ids dos professores da camada, ordenados por nome
#   outros        ids de professores de outros institutos ligados à camada, ordenados por nome
#   externos      ids EXT-L/EXT-N ligados à camada, em ordem alfabética
#   pares         {(id1, id2): {dimensão: [atividades]}}; id1 é sempre da camada
#   selecionadas  atividades que entram no dataset, já com o código


def montar_rede(atividades, professores):
    """Recebe atividades e professores e devolve a rede da camada com as atividades numeradas."""
    nome_por_id = {professor['id']: professor['nome'] for professor in professores}
    da_camada = [professor for professor in professores if professor['instituto'] == CAMADA]
    membros = [professor['id'] for professor in sorted(da_camada, key=chave_nome_professor)]
    pares = montar_pares(atividades, set(membros))
    outros, externos = [], set()
    for _, pessoa in pares:
        if pessoa.startswith('EXT-'):
            externos.add(pessoa)
        elif pessoa not in membros and pessoa not in outros:
            outros.append(pessoa)
    # Ordena por nome; em caso de nome igual, vale a ordem em que apareceram nos pares.
    decorados = []
    for ordem, pessoa in enumerate(outros):
        decorados.append((normalizar(nome_por_id[pessoa]), ordem, pessoa))
    decorados.sort()
    rede = {'membros': membros, 'outros': [pessoa for _, _, pessoa in decorados],
            'externos': sorted(externos), 'pares': pares}
    rede['selecionadas'] = numerar_atividades(atividades, rede)
    return rede


def chave_nome_professor(professor):
    """Ordena professores pelo nome normalizado (empates mantêm a ordem do cadastro)."""
    return normalizar(professor['nome'])


def montar_pares(atividades, membros):
    """Devolve os pares: cada professor da camada com cada outro participante identificado."""
    # Pares camada-camada aparecem nos dois sentidos (com o mesmo vetor); camada-outros e
    # camada-externo, uma vez. Nunca há auto-relação nem par com participante não identificado.
    # Um par só existe se tiver ao menos uma atividade que conta como colaboração
    # (colaboracao_valida): por isso nenhum par sai com o vetor todo zero.
    pares = {}
    for atividade in atividades:
        pessoas = list(atividade['participantes'])
        for pessoa in pessoas:
            if pessoa in membros:
                acrescentar_parceiros(pares, pessoa, pessoas, atividade)
    return pares


def acrescentar_parceiros(pares, pessoa, pessoas, atividade):
    """Acrescenta a atividade ao par (pessoa, parceiro) de cada outro participante."""
    for parceiro in pessoas:
        if parceiro == pessoa or not colaboracao_valida(atividade, pessoa, parceiro):
            continue
        if (pessoa, parceiro) not in pares:
            pares[(pessoa, parceiro)] = {dim: [] for dim in DIMENSOES}
        pares[(pessoa, parceiro)][atividade['dim']].append(atividade)


def colaboracao_valida(atividade, pessoa, parceiro):
    """A atividade conta como colaboração entre os dois? Orientação e banca dependem do papel."""
    papeis_pessoa = atividade['participantes'][pessoa]['papeis']
    papeis_parceiro = atividade['participantes'][parceiro]['papeis']
    if atividade['dim'] == 'ORI':
        return supervisor(papeis_pessoa) and supervisor(papeis_parceiro)
    if atividade['dim'] == 'BAN':
        return avaliador(papeis_pessoa) and avaliador(papeis_parceiro)
    return True


def supervisor(papeis):
    """Orientação: é orientador ou coorientador e não é o aluno (orientando)."""
    # Maria orienta o aluno João: não liga. Maria e Pedro orientam juntos o mesmo aluno: liga.
    if PAPEL_DE_ORIENTANDO in papeis:
        return False
    return len(papeis & PAPEIS_DE_SUPERVISAO) > 0


def avaliador(papeis):
    """Banca: é membro e nenhum papel tem 'candidato' (quem estava sendo avaliado não conta)."""
    # 'candidato/membro' acontece quando registros unificados deram papéis diferentes à mesma
    # pessoa: vale o de candidato.
    for papel in papeis:
        if PALAVRA_DE_CANDIDATO in papel:
            return False
    return PAPEL_DE_MEMBRO_DE_BANCA in papeis


def numerar_atividades(atividades, rede):
    """Escolhe as atividades do dataset e devolve-as numeradas por dimensão, ano e título."""
    # Entram as atividades com algum professor da camada ou de outro instituto ligado a ela
    # (estas são necessárias para as atividades individuais do dataset de entrada).
    professores_da_rede = set(rede['membros']) | set(rede['outros'])
    decoradas = []
    for ordem, atividade in enumerate(atividades):
        atividade['codigo'] = ''
        if any(pessoa in professores_da_rede for pessoa in atividade['participantes']):
            chave = (DIMENSOES.index(atividade['dim']), atividade['ano'] or '0000',
                     normalizar(atividade['titulo']), atividade['chave'], ordem)
            decoradas.append((chave, atividade))
    decoradas.sort()  # a chave termina na ordem original, então nunca há empate
    contagem = {dim: 0 for dim in DIMENSOES}
    selecionadas = []
    for _, atividade in decoradas:
        contagem[atividade['dim']] += 1
        atividade['codigo'] = f"{atividade['dim']}-{contagem[atividade['dim']]:06d}"
        selecionadas.append(atividade)
    return selecionadas


def vetor_bruto(por_dimensao):
    """Recebe {dimensão: [atividades]} e devolve os códigos de cada dimensão, ordenados."""
    vetor = []
    for dim in DIMENSOES:
        vetor.append(sorted(atividade['codigo'] for atividade in por_dimensao[dim]))
    return vetor


def tipo_de_relacao(parceiro, rede, instituto):
    """Devolve 'IMC-IMC', 'IMC-EXT' ou 'IMC-<instituto do parceiro>'."""
    if parceiro in rede['membros']:
        return f'{CAMADA}-{CAMADA}'
    if parceiro.startswith('EXT-'):
        return f'{CAMADA}-EXT'
    return f'{CAMADA}-{instituto}'
