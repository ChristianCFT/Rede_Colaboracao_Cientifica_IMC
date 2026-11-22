"""Etapa 2: extração de cada dimensão (ART, PTT, BAN, ORI, PRJ) a partir do texto de um item.

Recebe o texto já limpo de um item do Lattes e o item vazio; preenche título, ano,
participantes identificados e nomes não resolvidos.
"""
import re

from configuracao import SECAO_PROJETOS, TAMANHO_MAXIMO_DO_TEXTO
from src.externos import SUFIXOS_DE_NOME, compativel_com_abreviacao, separar_sobrenome_e_iniciais
from src.identificacao import citacao_especifica, professor_ou_externo_por_lattes, resolver_nome
from src.textos import forma_natural, limpar_espacos, normalizar_sem_particulas

# Cada item é um dicionário com as chaves:
#   dim, subtipo, fonte ('dono|subtipo|item n'), dono (id do dono do CV), doi, texto
#   titulo, ano, registro, candidato, aluno, papel_dono, periodo, situacao ('' se não se aplica)
#   participantes   [{'id', 'papel', 'metodo', 'nome'}] na ordem em que foram lidos
#   nao_resolvidos  [{'nome', 'motivo'}]       nomes_lidos  todos os nomes lidos no item

# Captura um ano entre 1900 e 2099 que não esteja grudado em outros dígitos.
ANO = re.compile(r'(?<!\d)((?:19|20)\d{2})(?!\d)')
# Captura o ano no padrão do Lattes: entre pontos, logo depois do título ('Título. 2016. Local').
ANO_DO_LATTES = re.compile(r'\.\s((?:19|20)\d{2})\.(?:\s|$)')
# Captura o ponto que separa a lista de autores do título ('SILVA, J. . Título').
FIM_DOS_AUTORES = re.compile(r'\s\.\s|\.\.\s|\.\s\.\s|\s\.$')
# Captura 'SOBRENOME, Iniciais. Resto' quando o primeiro autor vem colado no título.
AUTOR_E_RESTO = re.compile(r"^([^,;]{2,40},\s*(?:[A-ZÀ-Ý][\wÀ-ÿ'\-]*\.?\s*){1,6}?)\.\s+(.*)$")
# Captura o título e o DOI escondidos no atributo 'cvuri' dos artigos.
TITULO_NO_CVURI = re.compile(r'titulo=(.*?)&sequencial=')
DOI_NO_CVURI = re.compile(r'doi=(.*?)&')
# Captura o fim do título de um trabalho em anais ('Título. In: Congresso').
INICIO_DOS_ANAIS = re.compile(r'\.\s+In:\s')
# Captura o ano do congresso logo depois de 'In: Nome do evento, 2021,'.
ANO_DOS_ANAIS = re.compile(r'\bIn:\s.*?,\s*((?:19|20)\d{2})\s*,')
# Captura o número de registro de patentes, softwares e comissões.
NUMERO_DO_REGISTRO = re.compile(r'Número do registro:\s*([A-Z0-9][A-Z0-9.\-/ ]+?)\s*,')
# Captura tudo que não é letra nem dígito (limpa o número de registro).
NAO_PALAVRA = re.compile(r'\W')
# Captura o trecho fixo que separa os membros da banca do nome do candidato.
INICIO_DO_CANDIDATO = re.compile(r'Participação em banca de\s+')
# Captura o papel do dono numa orientação ('Orientador:' ou 'Coorientador:').
PAPEL_NA_ORIENTACAO = re.compile(r'(Co-?orientador|Orientador)\s*:\s*([^.]+)', re.I)
# Captura os 16 dígitos do Lattes iD no link do aluno.
DIGITOS_DO_LATTES = re.compile(r'(\d{16})')
# Capturam a situação e os integrantes de um projeto de pesquisa. A lista de integrantes para
# antes de 'Financiador(es)' ou 'Número de produções', com ou sem quebra de linha antes deles
# ('... - Integrante.Financiador(es): ...').
SITUACAO = re.compile(r'Situação:\s*([^;\n]+)')
INTEGRANTES = re.compile(
    r'Integrantes:\s*(.+?)(?:\.\s*\n|\.\s*$|\.?\s*Financiador|\.?\s*Número)', re.S)
# Captura o período no começo da célula de um projeto ('2019 - Atual').
INICIO_DO_PERIODO = re.compile(r'^\d{4}')
# Captura tudo que não é letra (com acento) nem dígito, na palavra antes de um ponto.
NAO_LETRA = re.compile(r'[^\wÀ-ÿ]')
MAXIMO_AUTOR, MAXIMO_AUTOR_SEM_PONTO = 90, 60  # tamanho máximo de um autor (com e sem ' . ')


def novo_item(dim, subtipo, fonte, dono, doi, texto):
    """Recebe os dados fixos de um item e devolve o dicionário com as demais chaves vazias."""
    return {'dim': dim, 'subtipo': subtipo, 'fonte': fonte, 'dono': dono, 'doi': doi,
            'texto': texto, 'titulo': '', 'ano': '', 'registro': '', 'candidato': '', 'aluno': '',
            'papel_dono': '', 'periodo': '', 'situacao': '', 'participantes': [],
            'nao_resolvidos': [], 'nomes_lidos': []}


def extrair_artigo(item, texto, cvuri, ano_oculto, links, professor, chaves_dono, indice):
    """ART: em periódico o título vem do cvuri; em anais, é o texto antes do 'In:'."""
    autores, resto = separar_autores(texto)
    if item['subtipo'].startswith('Artigo'):
        achado = TITULO_NO_CVURI.search(cvuri)
        titulo = achado.group(1).strip() if achado else ''
        achado = DOI_NO_CVURI.search(cvuri)
        if achado and achado.group(1).strip() and not item['doi']:
            item['doi'] = achado.group(1).strip().lower()
        titulo = titulo or resto.split('. ')[0]
        ano = ano_oculto
    else:
        titulo = INICIO_DOS_ANAIS.split(resto, maxsplit=1)[0]
        achado = ANO_DOS_ANAIS.search(resto)
        ano = achado.group(1) if achado else ''
    if not ano:
        anos = ANO.findall(resto)
        ano = anos[-1] if anos else ''
    item['titulo'] = titulo.strip(' .')
    item['ano'] = ano
    resolver_nomes(item, autores, 'autor', links, professor, chaves_dono, indice)


def extrair_producao_tecnica(item, texto, links, professor, chaves_dono, indice):
    """PTT: autores, título, ano e número de registro (patentes e softwares registrados)."""
    autores, resto = separar_autores(texto)
    item['titulo'], item['ano'] = separar_titulo_e_ano(resto)
    item['registro'] = ler_registro(texto)
    resolver_nomes(item, autores, 'autor', links, professor, chaves_dono, indice)


def extrair_banca(item, texto, links, professor, chaves_dono, indice):
    """BAN: comissão julgadora (lista de membros) ou trabalho de conclusão (membros + candidato)."""
    if item['subtipo'].startswith('Comissão'):
        membros, resto = separar_autores(texto)
        item['titulo'], item['ano'] = separar_titulo_e_ano(resto)
        item['registro'] = ler_registro(texto)
        resolver_nomes(item, membros, 'membro', links, professor, chaves_dono, indice)
        return
    partes = INICIO_DO_CANDIDATO.split(texto, maxsplit=1)
    candidato = ''
    if len(partes) == 2:
        membros = [membro.strip(' .') for membro in partes[0].split(';') if membro.strip(' .')]
        candidato, resto = separar_nome_inicial(partes[1])
    else:
        membros, resto = separar_autores(texto)
    item['titulo'], item['ano'] = separar_titulo_e_ano(resto)
    item['candidato'] = candidato
    resolver_membros_da_banca(item, membros, candidato, links, professor, chaves_dono, indice)
    if not candidato:
        return
    # O candidato só entra com link Lattes ou sendo professor cadastrado, nunca por nome solto.
    pessoa, metodo = resolver_nome(candidato, links, None, set(), indice, exigir_lattes=True)
    if pessoa and pessoa != professor['id']:
        adicionar_participante(item, pessoa, 'candidato', metodo, candidato)


def resolver_membros_da_banca(item, membros, candidato, links, professor, chaves_dono, indice):
    """Como resolver_nomes, mas o aluno escrito na lista de membros entra como candidato."""
    # Alguns currículos listam o próprio aluno entre os membros ('...; FRANCISCO, C. S. L.
    # Participação em banca de Christopher de Souza Lima Francisco'): sem isso, o aluno viraria
    # avaliador e ganharia relação com a banca. O dono do currículo registrou a banca como
    # avaliador, então nunca é o candidato.
    for membro in membros:
        pessoa, metodo = resolver_nome(membro, links, professor['id'], chaves_dono, indice,
                                       lattes_dono=professor['lattes'])
        papel = 'membro'
        if pessoa != professor['id'] and eh_o_candidato(membro, candidato):
            papel = 'candidato'
        if pessoa:
            adicionar_participante(item, pessoa, papel, metodo, membro)
        else:
            adicionar_nao_resolvido(item, membro, metodo)


def eh_o_candidato(membro, candidato):
    """O nome na lista de membros é o próprio candidato ('FRANCISCO, C. S. L' = 'Christopher ... Francisco')?"""
    if not candidato:
        return False
    palavras = normalizar_sem_particulas(candidato).split()
    if normalizar_sem_particulas(forma_natural(membro)).split() == palavras:
        return True
    # Citação: precisa ser específica ('SILVA, B' não basta), o sobrenome dela tem que ser o último
    # do aluno ('Souza, L. E' não é 'Luigi de Souza Esquaella') e as iniciais têm que bater na ordem.
    sobrenomes, _ = separar_sobrenome_e_iniciais(membro)
    sem_sufixo = [palavra for palavra in palavras if palavra not in SUFIXOS_DE_NOME]
    if not citacao_especifica(membro) or not sobrenomes or not sem_sufixo:
        return False
    if sobrenomes[-1] != sem_sufixo[-1]:
        return False
    return compativel_com_abreviacao(membro, palavras)


def extrair_orientacao(item, elemento, texto, professor, indice):
    """ORI: aluno, título, ano e papel do dono; o aluno só entra com Lattes ou sendo professor."""
    aluno, resto = separar_nome_inicial(texto)
    item['titulo'], item['ano'] = separar_titulo_e_ano(resto)
    item['aluno'] = aluno
    achado = PAPEL_NA_ORIENTACAO.search(texto)
    item['papel_dono'] = 'orientador'
    if achado and achado.group(1).lower().startswith('co'):
        item['papel_dono'] = 'coorientador'
    elif not achado:
        item['papel_dono'] = 'orientador (não especificado)'
    if not aluno:
        return
    icone = elemento.find('a', class_='icone-lattes')
    achado = DIGITOS_DO_LATTES.search(icone.get('href') or '') if icone else None
    if achado:
        pessoa = professor_ou_externo_por_lattes(achado.group(1), aluno, indice)
        metodo = 'lattes_id'
    else:
        pessoa, metodo = resolver_nome(aluno, {}, None, set(), indice, exigir_lattes=True)
    if pessoa and pessoa != professor['id']:
        adicionar_participante(item, pessoa, 'orientando', metodo, aluno)
    elif not pessoa:
        adicionar_nao_resolvido(item, aluno, metodo)


def extrair_projetos(bloco, professor, chaves_dono, indice):
    """PRJ: recebe o bloco 'Projetos de pesquisa' inteiro e devolve um item por projeto."""
    itens = []
    for numero, projeto in enumerate(ler_projetos(bloco), 1):
        achado = SITUACAO.search(projeto['detalhes'])
        situacao = achado.group(1).strip() if achado else ''
        achado = INTEGRANTES.search(projeto['detalhes'])
        integrantes = limpar_espacos(achado.group(1)) if achado else ''
        texto = f"{projeto['titulo']} | {projeto['periodo']} | Integrantes: {integrantes}"
        fonte = f"{professor['id']}|{SECAO_PROJETOS}|item {numero}"
        item = novo_item('PRJ', 'Projeto de pesquisa', fonte, professor['id'], '',
                         texto[:TAMANHO_MAXIMO_DO_TEXTO])
        item.update({'titulo': projeto['titulo'], 'ano': projeto['periodo'][:4],
                     'periodo': projeto['periodo'], 'situacao': situacao,
                     'papel_dono': 'integrante'})
        resolver_integrantes(item, integrantes, professor, chaves_dono, indice)
        finalizar_item(item, professor)
        itens.append(item)
    return itens


def ler_projetos(bloco):
    """Recebe o bloco de projetos e devolve [{'periodo', 'titulo', 'detalhes'}]."""
    # Cada projeto é uma célula 'layout-cell-3' com o período seguida de uma 'layout-cell-9'
    # com o título; as células 'layout-cell-9' seguintes trazem os detalhes.
    projetos, atual, periodo = [], None, ''
    for celula in bloco.find_all('div', class_=['layout-cell-3', 'layout-cell-9']):
        if 'layout-cell-3' in celula.get('class'):
            periodo = limpar_espacos(celula.get_text(' '))
            continue
        if periodo and INICIO_DO_PERIODO.match(periodo):
            titulo = limpar_espacos(celula.get_text(' '))
            atual = {'periodo': periodo, 'titulo': titulo, 'detalhes': ''}
            projetos.append(atual)
        elif atual is not None:
            atual['detalhes'] += ' ' + celula.get_text('\n')
        periodo = ''
    return projetos


def resolver_integrantes(item, integrantes, professor, chaves_dono, indice):
    """Recebe 'Nome - Coordenador / Nome - Integrante' e identifica cada integrante e papel."""
    for parte in integrantes.split(' / '):
        parte = parte.strip()
        if not parte:
            continue
        nome, papel = parte.rsplit(' - ', 1) if ' - ' in parte else (parte, '')
        papel = papel.strip(' .').lower() or 'integrante'
        pessoa, metodo = resolver_nome(nome, {}, professor['id'], chaves_dono, indice,
                                       lattes_dono=professor['lattes'])
        if not pessoa:
            adicionar_nao_resolvido(item, nome.strip(), metodo)
            continue
        if pessoa == professor['id']:
            item['papel_dono'] = papel
        adicionar_participante(item, pessoa, papel, metodo, nome.strip())


def resolver_nomes(item, nomes, papel, links, professor, chaves_dono, indice):
    """Identifica cada nome da lista e o grava como participante ou como não resolvido."""
    for nome in nomes:
        pessoa, metodo = resolver_nome(nome, links, professor['id'], chaves_dono, indice,
                                       lattes_dono=professor['lattes'])
        if pessoa:
            adicionar_participante(item, pessoa, papel, metodo, nome)
        else:
            adicionar_nao_resolvido(item, nome, metodo)


def adicionar_participante(item, pessoa, papel, metodo, nome):
    """Grava um participante identificado (e o nome lido, usado depois na deduplicação)."""
    item['participantes'].append({'id': pessoa, 'papel': papel, 'metodo': metodo, 'nome': nome})
    item['nomes_lidos'].append(nome)


def adicionar_nao_resolvido(item, nome, motivo):
    """Grava um nome que não virou identidade, com o motivo."""
    item['nao_resolvidos'].append({'nome': nome, 'motivo': motivo})
    item['nomes_lidos'].append(nome)


def finalizar_item(item, professor):
    """Garante o dono do CV entre os participantes e deixa cada pessoa uma vez só."""
    dono = professor['id']
    # O dono sempre participa do que registrou, mesmo quando o nome dele não foi reconhecido.
    if dono not in [participante['id'] for participante in item['participantes']]:
        papel = item['papel_dono'] or ('membro' if item['dim'] == 'BAN' else 'autor')
        adicionar_participante(item, dono, papel, 'dono_do_cv', professor['nome'])
    unicos, vistos = [], set()
    for participante in item['participantes']:
        if participante['id'] == dono and item['dim'] == 'ORI':
            participante['papel'] = item['papel_dono']
        if participante['id'] not in vistos:
            vistos.add(participante['id'])
            unicos.append(participante)
    item['participantes'] = unicos


def ler_registro(texto):
    """Recebe o texto do item e devolve o número de registro só com letras e dígitos."""
    achado = NUMERO_DO_REGISTRO.search(texto)
    return NAO_PALAVRA.sub('', achado.group(1)).upper() if achado else ''


def separar_autores(texto):
    """Recebe 'AUTOR1; AUTOR2 . Título...' e devolve ([autores], resto do texto)."""
    for achado in FIM_DOS_AUTORES.finditer(texto):
        antes, depois = texto[:achado.start()], texto[achado.end():]
        if depois.lstrip().startswith(';'):
            continue
        autores = [autor.strip(' .') for autor in antes.split(';') if autor.strip(' .')]
        if autores and max(len(autor) for autor in autores) <= MAXIMO_AUTOR:
            return autores, depois.strip()
        break
    return separar_autores_sem_ponto(texto)


def separar_autores_sem_ponto(texto):
    """Plano B, sem ' . ': devolve os pedaços curtos entre ';' antes do título e o resto."""
    pedacos = texto.split(';')
    autores = []
    for i, pedaco in enumerate(pedacos):
        pedaco = pedaco.strip()
        parece_nome = ',' in pedaco[:35] or len(pedaco.split()) <= 4
        if i < len(pedacos) - 1 and len(pedaco) <= MAXIMO_AUTOR_SEM_PONTO and parece_nome:
            autores.append(pedaco.strip(' .'))
            continue
        achado = AUTOR_E_RESTO.match(pedaco)
        if achado and i == 0:
            autores.append(achado.group(1).strip(' .'))
            return autores, achado.group(2)
        return autores, ';'.join(pedacos[i:]).strip()
    return autores, ''


def separar_titulo_e_ano(resto):
    """Recebe 'Título. 2023. (Tipo).' e devolve (título, ano)."""
    titulo, ano = titulo_e_ano_pela_pontuacao(resto)
    # Números no meio do título ('Portaria no. 2074', 'Fleutiaux, 1920', 'NBR 8800') enganam a
    # regra da pontuação: quando o ano no padrão do Lattes é outro, vale o do Lattes.
    achado = ANO_DO_LATTES.search(resto)
    if achado and achado.group(1) != ano and len(resto[:achado.start()].strip(' .,')) > 3:
        return resto[:achado.start()].rstrip(' .,'), achado.group(1)
    return titulo, ano


def titulo_e_ano_pela_pontuacao(resto):
    """O título vai até o primeiro ano que vem logo depois de um ponto ou de uma vírgula."""
    for achado in ANO.finditer(resto):
        antes = resto[:achado.start()].rstrip()
        if antes.endswith(('.', ',')) and len(antes) > 3:
            return antes.rstrip(' .,'), achado.group(1)
    achado = ANO.search(resto)
    return resto.split('. ')[0].strip(' .'), (achado.group(1) if achado else '')


def separar_nome_inicial(texto):
    """Recebe 'Ana M. Silva. Título...' e devolve (nome, resto), cortando no 1º ponto final."""
    # Um ponto depois de uma letra só ('M.') é de inicial e não corta o nome.
    for posicao in range(3, len(texto)):
        if texto[posicao] != '.':
            continue
        palavras = texto[:posicao].split()
        anterior = NAO_LETRA.sub('', palavras[-1]) if palavras else ''
        if len(anterior) >= 2 or texto[posicao + 1:posicao + 2] == '.':
            return texto[:posicao].strip(' .'), texto[posicao:].lstrip('. ')
    return '', texto
