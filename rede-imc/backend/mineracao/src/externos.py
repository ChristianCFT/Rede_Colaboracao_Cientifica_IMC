"""Etapa 3 (fim): externos que na verdade são professores, com dois ids ou com o nome do meio faltando.

Recebe os itens, os professores e o índice com os externos criados na leitura; corrige os
participantes dos itens no lugar.
"""
import re

from configuracao import COAUTORES_EM_COMUM_PARA_JUNTAR
from src.identificacao import esta_abreviado
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
    item['participantes'] = sem_repetidos(novos)


def sem_repetidos(participantes):
    """Deixa cada pessoa uma vez só no item (vale a primeira vez que ela aparece)."""
    unicos, vistos = [], set()
    for participante in participantes:
        if participante['id'] not in vistos:
            vistos.add(participante['id'])
            unicos.append(participante)
    return unicos


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


# ------------------------------------------------------------------- mesmo externo com dois ids
def unificar_externos_por_nome(itens, indice):
    """Troca cada EXT-N pelo EXT-L da mesma pessoa; devolve (quantos juntou, avisos)."""
    # A mesma pessoa vira EXT-L num currículo (com link do Lattes) e EXT-N em outro (só o nome).
    # O Lattes é a identificação mais confiável: se o nome completo do EXT-N pertence a um único
    # EXT-L, o EXT-N passa a ser o EXT-L. Nome de dois EXT-L não junta. Lattes suspeito fica
    # fora da comparação. Os dois casos viram aviso para revisão. Nome abreviado nunca junta.
    # Esta é a única junção de externos por nome: depois daqui nenhuma etapa troca ids.
    externos = indice['externos']
    em_uso = sorted(ids_dos_participantes(itens))
    lattes_por_nome, avisos = {}, []
    for identificador in em_uso:
        if identificador.startswith('EXT-L'):
            nomes = nomes_completos(externos[identificador])
            if lattes_suspeito(nomes):
                exemplos = ', '.join(sorted(nomes)[:3])
                avisos.append(f'Lattes {identificador} ligado a pessoas diferentes ({exemplos}...); '
                              'fora da junção por nome')
                continue
            for nome in nomes:
                lattes_por_nome.setdefault(nome, set()).add(identificador)
    trocas = {}
    for identificador in em_uso:
        if not identificador.startswith('EXT-N'):
            continue
        alvos = set()
        for nome in nomes_completos(externos[identificador]):
            alvos |= lattes_por_nome.get(nome, set())
        if len(alvos) == 1:
            trocas[identificador] = min(alvos)
        elif len(alvos) > 1:
            nome = externos[identificador]['nomes'].most_common(1)[0][0]
            avisos.append(f"{nome} ({identificador}): mais de um Lattes com esse nome "
                          f"({', '.join(sorted(alvos))}); não juntado")
    trocar_ids(itens, externos, trocas)
    return len(trocas), sorted(avisos)


def trocar_ids(itens, externos, trocas):
    """Aplica as junções {id que sai: id que fica}: soma os nomes vistos e troca o id nos itens."""
    for antigo, novo in trocas.items():
        externos[novo]['nomes'].update(externos.pop(antigo)['nomes'])
    for item in itens:
        for participante in item['participantes']:
            participante['id'] = trocas.get(participante['id'], participante['id'])
        item['participantes'] = sem_repetidos(item['participantes'])


def ids_dos_participantes(itens):
    """Devolve o conjunto de ids que aparecem nos itens."""
    ids = set()
    for item in itens:
        for participante in item['participantes']:
            ids.add(participante['id'])
    return ids


def nomes_completos(externo):
    """Devolve os nomes completos (sem abreviação) já vistos do externo, na ordem natural."""
    # Sem partículas, como no id EXT-N: 'Carolina de Aguiar Ferreira' = 'Carolina Aguiar Ferreira'.
    nomes = set()
    for nome in externo['nomes']:
        chave = normalizar_sem_particulas(forma_natural(nome))
        if not esta_abreviado(nome) and chave:
            nomes.add(chave)
    return nomes


def lattes_suspeito(nomes):
    """Dois nomes completos do mesmo Lattes sem nenhuma palavra em comum: são pessoas diferentes."""
    # Acontece quando o link do Lattes de um item está errado (o mesmo link em vários coautores).
    # Variações da mesma pessoa sempre dividem alguma palavra ('TIAGO FILHO', 'GERALDO TIAGO FILHO').
    palavras = []
    for nome in sorted(nomes):
        palavras.append(set(nome.split()) - PARTICULAS)
    for i in range(len(palavras)):
        for j in range(i + 1, len(palavras)):
            if not palavras[i] & palavras[j]:
                return True
    return False


# ------------------------------------------------------------------- nome do meio faltando
def unificar_nomes_do_meio(itens, indice):
    """Junta o externo cujo nome é o de outro sem algum nome do meio; devolve (quantos juntou, avisos)."""
    # 'Jorge Sotomayor Tello' e 'Jorge Manuel Sotomayor Tello' são a mesma pessoa quando: mesmo
    # primeiro e último nome, todas as palavras do nome curto estão no longo, nenhum é abreviado
    # e os dois têm coautor em comum (sem nunca aparecerem juntos no mesmo item). Nome curto que
    # cabe em dois nomes longos não junta; dois Lattes nunca juntam. Os dois casos viram aviso.
    externos = indice['externos']
    longos_por_curto = nomes_mais_longos(nomes_comparaveis(itens, externos), coautores_dos_externos(itens))
    trocas, avisos = {}, []
    for curto, longos in sorted(longos_por_curto.items()):
        nome = externos[curto]['nomes'].most_common(1)[0][0]
        if len(longos) > 1:
            avisos.append(f"{nome} ({curto}): cabe em mais de um nome ({', '.join(longos)}); não juntado")
        elif curto.startswith('EXT-L') and longos[0].startswith('EXT-L'):
            avisos.append(f'{nome} ({curto}) e {longos[0]}: dois Lattes com nomes parecidos; não juntado')
        elif curto.startswith('EXT-L'):
            trocas[longos[0]] = curto  # fica o id do Lattes
        else:
            trocas[curto] = longos[0]
    # Junção em cadeia (A -> B e B -> C) fica de fora: só junta direto no id que permanece.
    trocas = {antigo: novo for antigo, novo in trocas.items() if novo not in trocas}
    trocar_ids(itens, externos, trocas)
    return len(trocas), sorted(avisos)


def nomes_comparaveis(itens, externos):
    """{id: nomes completos} dos externos em uso que podem ser comparados por nome."""
    # Fica de fora o Lattes suspeito e o externo com nome que já é de outro externo (homônimos
    # ou nome de dois Lattes, já avisados na junção anterior).
    nomes = {}
    for identificador in sorted(ids_dos_participantes(itens)):
        if not identificador.startswith('EXT-'):
            continue
        completos = nomes_completos(externos[identificador])
        if identificador.startswith('EXT-L') and lattes_suspeito(completos):
            continue
        nomes[identificador] = completos
    donos = {}
    for identificador, completos in nomes.items():
        for nome in completos:
            donos.setdefault(nome, set()).add(identificador)
    comparaveis = {}
    for identificador, completos in nomes.items():
        if all(len(donos[nome]) == 1 for nome in completos):
            comparaveis[identificador] = completos
    return comparaveis


def coautores_dos_externos(itens):
    """{id do externo: ids de todos que aparecem com ele em algum item}."""
    coautores = {}
    for item in itens:
        ids = {participante['id'] for participante in item['participantes']}
        for identificador in ids:
            if identificador.startswith('EXT-'):
                coautores.setdefault(identificador, set()).update(ids - {identificador})
    return coautores


def nomes_mais_longos(nomes, coautores):
    """{id: [ids cujo nome contém o dele, com o mesmo primeiro e último nome e coautor em comum]}."""
    por_pontas = {}
    for identificador, completos in nomes.items():
        for nome in completos:
            palavras = nome.split()
            if len(palavras) >= 2:
                chave = (palavras[0], palavras[-1])
                por_pontas.setdefault(chave, []).append((identificador, set(palavras)))
    longos = {}
    for grupo in por_pontas.values():
        for curto, palavras_curto in grupo:
            for longo, palavras_longo in grupo:
                if curto != longo and palavras_curto < palavras_longo and mesma_pessoa(curto, longo, coautores):
                    longos.setdefault(curto, set()).add(longo)
    return {curto: sorted(ids) for curto, ids in longos.items()}


def mesma_pessoa(curto, longo, coautores):
    """Têm coautores em comum e nunca aparecem juntos no mesmo item (aí seriam duas pessoas)?"""
    do_curto, do_longo = coautores.get(curto, set()), coautores.get(longo, set())
    if longo in do_curto:
        return False
    return len(do_curto & do_longo) >= COAUTORES_EM_COMUM_PARA_JUNTAR
