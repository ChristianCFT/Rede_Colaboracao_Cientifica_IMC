# etapa 5: monta a rede do IMC (pares, atividades e vetores)
from configuracao import (CAMADA, DIMENSOES, PALAVRA_DE_CANDIDATO, PAPEIS_DE_SUPERVISAO,
                          PAPEL_DE_MEMBRO_DE_BANCA, PAPEL_DE_ORIENTANDO)
from src.textos import normalizar

# rede: membros, outros, externos, selecionadas e pares {(id1, id2): {dim: [atividades]}}
# id1 é sempre da camada


def montar_rede(atividades, professores):
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
    # ordena por nome
    decorados = []
    for ordem, pessoa in enumerate(outros):
        decorados.append((normalizar(nome_por_id[pessoa]), ordem, pessoa))
    decorados.sort()
    rede = {'membros': membros, 'outros': [pessoa for _, _, pessoa in decorados],
            'externos': sorted(externos), 'pares': pares}
    rede['selecionadas'] = numerar_atividades(atividades, rede)
    return rede


def chave_nome_professor(professor):
    return normalizar(professor['nome'])


def montar_pares(atividades, membros):
    # par só existe se tiver pelo menos uma colaboração válida (sem auto-relação)
    pares = {}
    for atividade in atividades:
        pessoas = list(atividade['participantes'])
        for pessoa in pessoas:
            if pessoa in membros:
                acrescentar_parceiros(pares, pessoa, pessoas, atividade)
    return pares


def acrescentar_parceiros(pares, pessoa, pessoas, atividade):
    for parceiro in pessoas:
        if parceiro == pessoa or not colaboracao_valida(atividade, pessoa, parceiro):
            continue
        if (pessoa, parceiro) not in pares:
            pares[(pessoa, parceiro)] = {dim: [] for dim in DIMENSOES}
        pares[(pessoa, parceiro)][atividade['dim']].append(atividade)


def colaboracao_valida(atividade, pessoa, parceiro):
    """orientação e banca dependem do papel"""
    papeis_pessoa = atividade['participantes'][pessoa]['papeis']
    papeis_parceiro = atividade['participantes'][parceiro]['papeis']
    if atividade['dim'] == 'ORI':
        return supervisor(papeis_pessoa) and supervisor(papeis_parceiro)
    if atividade['dim'] == 'BAN':
        return avaliador(papeis_pessoa) and avaliador(papeis_parceiro)
    return True


def supervisor(papeis):
    # Maria orienta João: não liga. Maria e Pedro orientam o mesmo aluno: liga
    if PAPEL_DE_ORIENTANDO in papeis:
        return False
    return len(papeis & PAPEIS_DE_SUPERVISAO) > 0


def avaliador(papeis):
    # 'candidato/membro': vale candidato
    for papel in papeis:
        if PALAVRA_DE_CANDIDATO in papel:
            return False
    return PAPEL_DE_MEMBRO_DE_BANCA in papeis


def numerar_atividades(atividades, rede):
    # entram as atividades com professor da camada ou de outro instituto ligado a ela
    professores_da_rede = set(rede['membros']) | set(rede['outros'])
    decoradas = []
    for ordem, atividade in enumerate(atividades):
        atividade['codigo'] = ''
        if any(pessoa in professores_da_rede for pessoa in atividade['participantes']):
            chave = (DIMENSOES.index(atividade['dim']), atividade['ano'] or '0000',
                     normalizar(atividade['titulo']), atividade['chave'], ordem)
            decoradas.append((chave, atividade))
    decoradas.sort()  # nunca empata
    contagem = {dim: 0 for dim in DIMENSOES}
    selecionadas = []
    for _, atividade in decoradas:
        contagem[atividade['dim']] += 1
        atividade['codigo'] = f"{atividade['dim']}-{contagem[atividade['dim']]:06d}"
        selecionadas.append(atividade)
    return selecionadas


def vetor_bruto(por_dimensao):
    vetor = []
    for dim in DIMENSOES:
        vetor.append(sorted(atividade['codigo'] for atividade in por_dimensao[dim]))
    return vetor


def tipo_de_relacao(parceiro, rede, instituto):
    """'IMC-IMC', 'IMC-EXT' ou 'IMC-<instituto>'"""
    if parceiro in rede['membros']:
        return f'{CAMADA}-{CAMADA}'
    if parceiro.startswith('EXT-'):
        return f'{CAMADA}-EXT'
    return f'{CAMADA}-{instituto}'
