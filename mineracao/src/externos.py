"""Etapa 3 (fim): externos que na verdade são professores da UNIFEI.

Recebe os itens, os professores e o índice com os externos criados na leitura; corrige os
participantes dos itens no lugar (não devolve nada).
"""
import re

from src.textos import PARTICULAS, forma_natural, normalizar, normalizar_sem_particulas

SUFIXOS_DE_NOME = {'JUNIOR', 'JR', 'FILHO', 'NETO', 'SOBRINHO'}
# Captura qualquer letra seguida de ponto (sinal de que o nome está abreviado).
LETRA_COM_PONTO = re.compile(r'\b\w\.')
# Método gravado quando um externo vira professor.
METODO_TROCA = 'lattes_id+nome_completo'


def corrigir_externos(itens, professores, indice):
    """Troca externos pelo professor certo ou os retira para revisão, em todos os itens."""
    # Evidência forte (Lattes iD desconhecido + nome completo de um professor sem Lattes):
    # o externo vira o professor. Nome só compatível: o nome vai para 'possivel_professor'.
    # Nunca se juntam pessoas só porque os nomes se parecem.
    trocas, suspeitos = encontrar_trocas(professores, indice['externos'])
    encontrar_suspeitos(professores, indice['externos'], trocas, suspeitos)
    for item in itens:
        aplicar_trocas(item, trocas, suspeitos)


def aplicar_trocas(item, trocas, suspeitos):
    """Corrige os participantes de um item e deixa cada pessoa uma vez só."""
    novos = []
    for participante in item['participantes']:
        if participante['id'] in trocas:
            novos.append({'id': trocas[participante['id']], 'papel': participante['papel'],
                          'metodo': METODO_TROCA, 'nome': participante['nome']})
        elif participante['id'] in suspeitos:
            nao_resolvido = {'nome': participante['nome'], 'motivo': 'possivel_professor'}
            item['nao_resolvidos'].append(nao_resolvido)
        else:
            novos.append(participante)
    unicos, vistos = [], set()
    for participante in novos:
        if participante['id'] not in vistos:
            vistos.add(participante['id'])
            unicos.append(participante)
    item['participantes'] = unicos


def encontrar_trocas(professores, externos):
    """Devolve ({EXT-L: id do professor}, {EXT-L suspeitos}) pelo nome completo dos professores."""
    ids = {professor['id']: professor for professor in professores}
    por_nome = professores_por_nome(professores)
    candidatos, suspeitos = {}, set()
    for identificador, externo in externos.items():
        if not identificador.startswith('EXT-L'):
            continue
        alvos = set()
        for nome in externo['nomes']:
            chave = normalizar_sem_particulas(forma_natural(nome))
            alvos |= por_nome.get(chave, set())
        alvos = {alvo for alvo in alvos if ids[alvo]['lattes'] in ('', externo['lattes'])}
        if len(alvos) == 1:
            candidatos.setdefault(min(alvos), []).append(identificador)
        elif len(alvos) > 1:
            suspeitos.add(identificador)
    trocas = {}
    for professor, lista in candidatos.items():
        # Dois Lattes para o mesmo nome: fica o mais frequente; o outro vai para revisão.
        ordenados = []
        for ordem, identificador in enumerate(lista):
            vezes = sum(externos[identificador]['nomes'].values())
            ordenados.append((-vezes, ordem, identificador))
        ordenados.sort()
        trocas[ordenados[0][2]] = professor
        for _, _, identificador in ordenados[1:]:
            suspeitos.add(identificador)
    return trocas, suspeitos


def professores_por_nome(professores):
    """Devolve {nome sem partículas: {ids}} com nome do CV, da pasta e do índice."""
    por_nome = {}
    for professor in professores:
        for nome in (professor['nome'], professor['pasta'], professor['nome_indice']):
            if nome:
                por_nome.setdefault(normalizar_sem_particulas(nome), set()).add(professor['id'])
    return por_nome


def encontrar_suspeitos(professores, externos, trocas, suspeitos):
    """Acrescenta aos suspeitos os externos cujo nome é compatível com algum professor."""
    trocados = set(trocas.values())
    palavras_professor = {}
    sem_lattes = []
    for professor in professores:
        palavras_professor[professor['id']] = normalizar_sem_particulas(professor['nome']).split()
        if not professor['lattes'] and professor['id'] not in trocados:
            sem_lattes.append(professor['id'])
    for identificador, externo in externos.items():
        if identificador in trocas or identificador in suspeitos:
            continue
        # Cada variante do nome é normalizada uma vez só (antes era uma vez por professor:
        # era o maior gasto de tempo no cProfile).
        variantes = []
        for nome in externo['nomes']:
            variantes.append((nome, normalizar_sem_particulas(forma_natural(nome)).split()))
        if identificador.startswith('EXT-L'):
            alvos = sem_lattes
        else:
            alvos = list(palavras_professor)
        for professor in alvos:
            if externo_compativel(identificador, variantes, palavras_professor[professor]):
                suspeitos.add(identificador)
                break


def externo_compativel(identificador, variantes, palavras_professor):
    """EXT-L: todas as variantes batem com o professor; EXT-N: basta uma bater pelo nome."""
    if identificador.startswith('EXT-N'):
        for _, palavras in variantes:
            if compativel_com_nome_completo(palavras, palavras_professor):
                return True
        return False
    for nome, palavras in variantes:
        if ',' in nome or LETRA_COM_PONTO.search(nome):
            if not compativel_com_abreviacao(nome, palavras_professor):
                return False
        elif not compativel_com_nome_completo(palavras, palavras_professor):
            return False
    return True


def compativel_com_nome_completo(palavras, palavras_professor):
    """Mesmo primeiro nome e (mesmo último nome ou um conjunto de palavras contido no outro)."""
    if len(palavras) < 2 or len(palavras_professor) < 2:
        return False
    if palavras[0] != palavras_professor[0]:
        return False
    conjunto, do_professor = set(palavras), set(palavras_professor)
    if palavras[-1] == palavras_professor[-1]:
        return True
    return do_professor <= conjunto or conjunto <= do_professor


def compativel_com_abreviacao(citacao, palavras_professor):
    """'SILVA, J. C.' bate com 'João Carlos Silva': sobrenome presente e iniciais na ordem."""
    if not palavras_professor:
        return False
    sobrenomes, iniciais = separar_sobrenome_e_iniciais(citacao)
    if not sobrenomes or sobrenomes[-1] not in palavras_professor or not iniciais:
        return False
    resto = []
    for palavra in palavras_professor:
        if palavra not in sobrenomes and palavra not in SUFIXOS_DE_NOME:
            resto.append(palavra)
    if not resto or not inicial_bate(iniciais[0], resto[0]):
        return False
    # As demais iniciais precisam aparecer depois, na mesma ordem, entre os prenomes.
    posicao = 1
    for inicial in iniciais[1:]:
        while posicao < len(resto) and not inicial_bate(inicial, resto[posicao]):
            posicao += 1
        if posicao >= len(resto):
            return False
        posicao += 1
    return True


def separar_sobrenome_e_iniciais(citacao):
    """Recebe 'SILVA, J. C.' (ou 'J. C. Silva') e devolve (['SILVA'], ['J', 'C'])."""
    if ',' in citacao:
        sobrenome, prenomes = citacao.split(',', 1)
    else:
        partes = citacao.replace('.', '. ').split()
        sobrenome, prenomes = citacao, ''
        if len(partes) > 1:
            sobrenome, prenomes = partes[-1], ' '.join(partes[:-1])
    sobrenomes = []
    for palavra in normalizar(sobrenome).split():
        if palavra not in PARTICULAS and palavra not in SUFIXOS_DE_NOME:
            sobrenomes.append(palavra)
    iniciais = []
    for palavra in normalizar(prenomes).split():
        if not (len(palavra) > 1 and palavra in PARTICULAS):
            iniciais.append(palavra)
    return sobrenomes, iniciais


def inicial_bate(inicial, palavra):
    """Uma letra bate com a palavra que começa por ela; um prenome inteiro precisa ser igual."""
    if len(inicial) > 1:
        return palavra == inicial
    return palavra[0] == inicial
