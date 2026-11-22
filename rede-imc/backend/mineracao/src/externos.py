# etapa 3: corrige externos que são professores, duplicados ou com nome do meio faltando
import re

from configuracao import COAUTORES_EM_COMUM_PARA_JUNTAR
from src.identificacao import esta_abreviado
from src.textos import PARTICULAS, forma_natural, normalizar, normalizar_sem_particulas

SUFIXOS_DE_NOME = {'JUNIOR', 'JR', 'FILHO', 'NETO', 'SOBRINHO'}
# letra seguida de ponto = nome abreviado
LETRA_COM_PONTO = re.compile(r'\b\w\.')
METODO_TROCA = 'lattes_id+nome_completo'


def corrigir_externos(itens, professores, indice):
    # só troca com evidência forte (Lattes + nome completo); nome parecido vai pra revisão
    trocas, suspeitos = encontrar_trocas(professores, indice['externos'])
    encontrar_suspeitos(professores, indice['externos'], trocas, suspeitos)
    for item in itens:
        aplicar_trocas(item, trocas, suspeitos)


def aplicar_trocas(item, trocas, suspeitos):
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
    """vale a primeira vez que aparece"""
    unicos, vistos = [], set()
    for participante in participantes:
        if participante['id'] not in vistos:
            vistos.add(participante['id'])
            unicos.append(participante)
    return unicos


def encontrar_trocas(professores, externos):
    """devolve ({EXT-L: professor}, {EXT-L suspeitos})"""
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
        # dois Lattes pro mesmo nome: fica o mais frequente
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
    por_nome = {}
    for professor in professores:
        for nome in (professor['nome'], professor['pasta'], professor['nome_indice']):
            if nome:
                por_nome.setdefault(normalizar_sem_particulas(nome), set()).add(professor['id'])
    return por_nome


def encontrar_suspeitos(professores, externos, trocas, suspeitos):
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
        # normaliza cada variante uma vez só (tava lento)
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
    """EXT-L: todas as variantes batem; EXT-N: basta uma"""
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
    if len(palavras) < 2 or len(palavras_professor) < 2:
        return False
    if palavras[0] != palavras_professor[0]:
        return False
    conjunto, do_professor = set(palavras), set(palavras_professor)
    if palavras[-1] == palavras_professor[-1]:
        return True
    return do_professor <= conjunto or conjunto <= do_professor


def compativel_com_abreviacao(citacao, palavras_professor):
    """'SILVA, J. C.' bate com 'João Carlos Silva'"""
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
    # as outras iniciais na mesma ordem
    posicao = 1
    for inicial in iniciais[1:]:
        while posicao < len(resto) and not inicial_bate(inicial, resto[posicao]):
            posicao += 1
        if posicao >= len(resto):
            return False
        posicao += 1
    return True


def separar_sobrenome_e_iniciais(citacao):
    """'SILVA, J. C.' -> (['SILVA'], ['J', 'C'])"""
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
    if len(inicial) > 1:
        return palavra == inicial
    return palavra[0] == inicial


# mesmo externo com dois ids
def unificar_externos_por_nome(itens, indice):
    """troca EXT-N pelo EXT-L da mesma pessoa"""
    # só junta se o nome completo for de um único EXT-L, nome abreviado nunca junta.
    # depois daqui ninguém mais troca id
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
    for antigo, novo in trocas.items():
        externos[novo]['nomes'].update(externos.pop(antigo)['nomes'])
    for item in itens:
        for participante in item['participantes']:
            participante['id'] = trocas.get(participante['id'], participante['id'])
        item['participantes'] = sem_repetidos(item['participantes'])


def ids_dos_participantes(itens):
    ids = set()
    for item in itens:
        for participante in item['participantes']:
            ids.add(participante['id'])
    return ids


def nomes_completos(externo):
    # sem partículas, igual ao id EXT-N
    nomes = set()
    for nome in externo['nomes']:
        chave = normalizar_sem_particulas(forma_natural(nome))
        if not esta_abreviado(nome) and chave:
            nomes.add(chave)
    return nomes


def lattes_suspeito(nomes):
    """mesmo Lattes com nomes sem nenhuma palavra em comum = pessoas diferentes"""
    # acontece quando o link do Lattes do item está errado
    palavras = []
    for nome in sorted(nomes):
        palavras.append(set(nome.split()) - PARTICULAS)
    for i in range(len(palavras)):
        for j in range(i + 1, len(palavras)):
            if not palavras[i] & palavras[j]:
                return True
    return False


# nome do meio faltando
def unificar_nomes_do_meio(itens, indice):
    # ex: 'Jorge Sotomayor Tello' e 'Jorge Manuel Sotomayor Tello'. precisa ter coautor
    # em comum e nunca aparecer junto no mesmo item
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
    # não junta em cadeia
    trocas = {antigo: novo for antigo, novo in trocas.items() if novo not in trocas}
    trocar_ids(itens, externos, trocas)
    return len(trocas), sorted(avisos)


def nomes_comparaveis(itens, externos):
    # tira Lattes suspeito e homônimos
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
    coautores = {}
    for item in itens:
        ids = {participante['id'] for participante in item['participantes']}
        for identificador in ids:
            if identificador.startswith('EXT-'):
                coautores.setdefault(identificador, set()).update(ids - {identificador})
    return coautores


def nomes_mais_longos(nomes, coautores):
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
    """coautor em comum e nunca juntos no mesmo item"""
    do_curto, do_longo = coautores.get(curto, set()), coautores.get(longo, set())
    if longo in do_curto:
        return False
    return len(do_curto & do_longo) >= COAUTORES_EM_COMUM_PARA_JUNTAR
