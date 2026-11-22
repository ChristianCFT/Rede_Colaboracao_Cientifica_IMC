"""Etapa 1: monta a lista de professores a partir dos índices .txt, das pastas e do cabeçalho do CV.

Recebe o ZIP com os currículos (ou a pasta já extraída) e devolve um dicionário por pasta de
professor, já com o id (SIAPE) que identifica a pessoa em todos os datasets.
"""
import datetime
import re
import zipfile

from bs4 import BeautifulSoup

from configuracao import PASTA_TEMPORARIOS, SIGLA_POR_PASTA
from src.indices import ler_indices_do_instituto
from src.textos import (chave_ordenacao, corrigir_escapes, hash_curto, ler_html, limpar_espacos,
                        normalizar, normalizar_sem_particulas)

# Cada professor é um dicionário com as chaves:
#   id           SIAPE; sem SIAPE, 'PROV-L' + Lattes iD ou 'PROV-N' + hash do nome
#   nome         nome do currículo, senão do índice, senão da pasta
#   instituto    sigla oficial (IMC, IFQ, ...)          pasta   nome da pasta no ZIP
#   html         caminho do HTML escolhido (None se a pasta não tem currículo)
#   lattes       Lattes iD de 16 dígitos ('' se desconhecido)
#   citacoes     formas de citação declaradas no CV     area    'Grande área / Área; ...'
#   siape, nome_indice, url_lattes    dados do índice .txt ('' se a pasta não casou)
#   registro     o registro do índice usado (ou None); nome_cv, lattes_cv, areas, atualizacao

# Captura o link completo do Lattes que já vem escrito no índice.
LINK_LATTES = re.compile(r'https?://lattes\.cnpq\.br/\d{16}')
# Captura 16 dígitos seguidos (o Lattes iD no bloco 'Identificação').
DEZESSEIS_DIGITOS = re.compile(r'(\d{16})')
# Captura a data de atualização do currículo.
ATUALIZACAO = re.compile(r'Última atualização do currículo em (\d{2}/\d{2}/\d{4})')
# Captura o Lattes iD no rodapé 'Endereço para acessar este CV'.
ENDERECO_DO_CV = re.compile(
    r'Endereço para acessar este CV:\s*(?:<[^>]+>)?\s*https?://lattes\.cnpq\.br/(\d{16})')
# Captura a grande área e a área de uma linha de 'Áreas de atuação'.
GRANDE_AREA = re.compile(r'Grande área:\s*([^/]+?)\s*/')
AREA = re.compile(r'/\s*Área:\s*([^/]+?)\s*(?:/|\.\s*$|$)')
LINK_LATTES_PADRAO = 'http://lattes.cnpq.br/'
LINK_LATTES_ANTIGO = 'http://buscatextual.cnpq.br/buscatextual/visualizacv.do?id='


def carregar_professores(raiz):
    """Recebe a pasta com os institutos e devolve a lista de professores com id."""
    professores, registros = [], []
    for pasta_instituto, sigla in listar_institutos(raiz):
        registros_instituto = ler_indices_do_instituto(pasta_instituto, sigla)
        registros += registros_instituto
        for pasta_professor in listar_subpastas(pasta_instituto):
            professores.append(montar_professor(pasta_professor, sigla, registros_instituto))
    for professor in professores:
        if professor['registro'] is None:
            casar_sem_particulas(professor, registros)
    for professor in professores:
        completar_professor(professor)
    conferir_ids_unicos(professores)
    return professores


def abrir_entrada(caminho):
    """Recebe o ZIP (ou uma pasta já extraída) e devolve a pasta com as pastas dos institutos."""
    pasta = caminho
    if not caminho.is_dir():
        pasta = PASTA_TEMPORARIOS / caminho.stem
        # Extrai só na primeira vez; se a extração for interrompida, apague a pasta e rode de novo.
        if not pasta.exists():
            print(f'   extraindo {caminho.name} em {pasta} ...')
            with zipfile.ZipFile(caminho) as arquivo_zip:
                arquivo_zip.extractall(pasta)
    for subpasta in pasta.iterdir():
        if subpasta.is_dir() and primeira_palavra(subpasta.name) in SIGLA_POR_PASTA:
            return pasta
    raise FileNotFoundError(f'nenhuma pasta de instituto reconhecida dentro de {pasta}')


def primeira_palavra(nome_pasta):
    """Recebe 'IMC - Instituto de ...' e devolve 'IMC' (a chave de SIGLA_POR_PASTA)."""
    return corrigir_escapes(nome_pasta).strip().split(' ')[0].strip()


def listar_institutos(raiz):
    """Recebe a pasta raiz e devolve [(pasta do instituto, sigla)] em ordem estável."""
    institutos = []
    for pasta in listar_subpastas(raiz):
        palavra = primeira_palavra(pasta.name)
        if palavra not in SIGLA_POR_PASTA:
            print(f'   aviso: pasta sem sigla conhecida ignorada: {corrigir_escapes(pasta.name)}')
            continue
        institutos.append((pasta, SIGLA_POR_PASTA[palavra]))
    return institutos


def listar_subpastas(pasta):
    """Recebe uma pasta e devolve as subpastas ordenadas por chave_ordenacao."""
    subpastas = [item for item in pasta.iterdir() if item.is_dir()]
    return sorted(subpastas, key=chave_do_caminho)


def chave_do_caminho(caminho):
    """Recebe um caminho e devolve a chave de ordenação do seu nome."""
    return chave_ordenacao(caminho.name)


def montar_professor(pasta, sigla, registros_instituto):
    """Recebe a pasta de um professor e devolve o professor com o índice e o cabeçalho do CV."""
    nome_pasta = corrigir_escapes(pasta.name).strip()
    candidatos = []
    for registro in registros_instituto:
        if normalizar(registro['nome']) == normalizar(nome_pasta):
            candidatos.append(registro)
    registro = None
    if len(candidatos) == 1:
        registro = candidatos[0]
        registro['usado'] = True
    lattes_indice = registro['lattes'] if registro else ''
    htmls = [item for item in pasta.iterdir() if item.name.lower().endswith(('.html', '.htm'))]
    html, cabecalho = escolher_html(sorted(htmls, key=chave_do_caminho), lattes_indice)
    professor = {'pasta': nome_pasta, 'instituto': sigla, 'registro': registro, 'html': html}
    professor.update(cabecalho)
    return professor


def escolher_html(htmls, lattes_indice):
    """Recebe os HTMLs de uma pasta e devolve (html escolhido, cabeçalho): um CV por professor."""
    if not htmls:
        return None, cabecalho_vazio()
    lidos = []
    for html in htmls:
        try:
            lidos.append((html, ler_cabecalho(html), True))
        except Exception:  # um currículo corrompido não interrompe a execução
            lidos.append((html, cabecalho_vazio(), False))
    if len(lidos) == 1:
        return lidos[0][0], lidos[0][1]
    validos = [lido for lido in lidos if lido[2]] or lidos
    # Critérios, em ordem: Lattes iD igual ao do índice, atualização mais recente, maior arquivo.
    escolhido, melhor_chave = None, None
    for html, cabecalho, _ in validos:
        mesmo_lattes = bool(lattes_indice) and cabecalho['lattes_cv'] == lattes_indice
        chave = (mesmo_lattes, ler_data(cabecalho['atualizacao']), html.stat().st_size)
        if escolhido is None or chave > melhor_chave:
            escolhido, melhor_chave = (html, cabecalho), chave
    return escolhido


def cabecalho_vazio():
    """Devolve o cabeçalho de quem não tem currículo legível."""
    return {'nome_cv': '', 'citacoes': [], 'lattes_cv': '', 'areas': [], 'atualizacao': ''}


def ler_data(texto):
    """Recebe '31/12/2025' e devolve a data; vazio ou inválido vira a menor data possível."""
    try:
        return datetime.datetime.strptime(texto, '%d/%m/%Y')
    except (TypeError, ValueError):
        return datetime.datetime.min


def ler_cabecalho(html):
    """Recebe o caminho do CV e devolve nome, citações, Lattes iD, áreas e data de atualização."""
    texto = ler_html(html)
    sopa = BeautifulSoup(texto, 'lxml')
    cabecalho = cabecalho_vazio()
    titulo = sopa.find('h2', class_='nome')
    if titulo:
        cabecalho['nome_cv'] = limpar_espacos(titulo.get_text(' '))
    identificacao = None
    for bloco in sopa.find_all('div', class_='title-wrapper'):
        h1 = bloco.find('h1')
        secao = limpar_espacos(h1.get_text()) if h1 else ''
        if secao == 'Identificação':
            identificacao = bloco
        if secao == 'Áreas de atuação':
            ler_areas(bloco, cabecalho)
    if identificacao:
        ler_identificacao(identificacao, cabecalho)
    achado = ATUALIZACAO.search(texto)
    if achado:
        cabecalho['atualizacao'] = achado.group(1)
    if not cabecalho['lattes_cv']:
        achado = ENDERECO_DO_CV.search(texto)
        cabecalho['lattes_cv'] = achado.group(1) if achado else ''
    return cabecalho


def ler_areas(bloco, cabecalho):
    """Recebe o bloco 'Áreas de atuação' e acrescenta cada linha não vazia ao cabeçalho."""
    for celula in bloco.find_all('div', class_='layout-cell-9'):
        area = limpar_espacos(celula.get_text(' '))
        if area:
            cabecalho['areas'].append(area)


def ler_identificacao(bloco, cabecalho):
    """Recebe o bloco 'Identificação' e preenche nome, citações e Lattes iD no cabeçalho."""
    # O bloco é uma lista de células: um rótulo ('Nome', 'Lattes iD'...) e, logo depois, o valor.
    celulas = bloco.find_all('div', class_='layout-cell-pad-5')
    for i in range(len(celulas) - 1):
        rotulo = limpar_espacos(celulas[i].get_text(' '))
        valor = celulas[i + 1]
        if rotulo == 'Nome':
            cabecalho['nome_cv'] = limpar_espacos(valor.get_text(' ')) or cabecalho['nome_cv']
        if rotulo.startswith('Nome em citações'):
            partes = [limpar_espacos(parte) for parte in valor.get_text().split(';')]
            cabecalho['citacoes'] = [parte for parte in partes if parte]
        if rotulo.startswith('Lattes iD'):
            achado = DEZESSEIS_DIGITOS.search(valor.get_text())
            cabecalho['lattes_cv'] = achado.group(1) if achado else cabecalho['lattes_cv']


def casar_sem_particulas(professor, registros):
    """Segunda tentativa de achar o professor no índice: nome sem partículas e sem acentos."""
    soltos = []
    for registro in registros:
        if not registro['usado'] and registro['sigla'] == professor['instituto']:
            soltos.append(registro)
    candidatos = registros_com_nome(soltos, professor['pasta'])
    if len(candidatos) != 1 and professor['nome_cv']:
        candidatos = registros_com_nome(soltos, professor['nome_cv'])
    if len(candidatos) == 1:
        candidatos[0]['usado'] = True
        professor['registro'] = candidatos[0]


def registros_com_nome(registros, nome):
    """Recebe registros e um nome e devolve os registros com o mesmo nome sem partículas."""
    alvo = normalizar_sem_particulas(nome)
    iguais = []
    for registro in registros:
        if normalizar_sem_particulas(registro['nome']) == alvo:
            iguais.append(registro)
    return iguais


def completar_professor(professor):
    """Preenche id, nome, SIAPE, Lattes, área e URL do Lattes a partir do índice e do CV."""
    registro = professor['registro'] or {'nome': '', 'lattes': '', 'lattes_k': '', 'siape': '',
                                         'texto': ''}
    professor['siape'] = registro['siape']
    professor['nome_indice'] = registro['nome']
    professor['lattes'] = professor['lattes_cv'] or registro['lattes']
    professor['nome'] = professor['nome_cv'] or registro['nome'] or professor['pasta']
    if professor['siape']:
        professor['id'] = professor['siape']
    elif professor['lattes']:
        professor['id'] = 'PROV-L' + professor['lattes']
    else:
        professor['id'] = 'PROV-N' + hash_curto(normalizar(professor['nome']))
    professor['area'] = formatar_areas(professor['areas'])
    professor['url_lattes'] = montar_url_lattes(registro, professor['lattes'])


def formatar_areas(areas):
    """Recebe as linhas de 'Áreas de atuação' e devolve 'Grande área / Área' únicos, com '; '."""
    vistos = []
    for linha in areas:
        grande, area = GRANDE_AREA.search(linha), AREA.search(linha)
        grande = grande.group(1).strip().rstrip('.') if grande else ''
        area = area.group(1).strip().rstrip('.') if area else ''
        texto = f'{grande} / {area}' if grande and area else (grande or area)
        if texto and texto not in vistos:
            vistos.append(texto)
    return '; '.join(vistos)


def montar_url_lattes(registro, lattes):
    """Devolve o link do índice; senão o link pelo Lattes iD; senão o link antigo 'K...'."""
    achado = LINK_LATTES.search(registro['texto'])
    if achado:
        return achado.group(0)
    if lattes:
        return LINK_LATTES_PADRAO + lattes
    if registro['lattes_k']:
        return LINK_LATTES_ANTIGO + registro['lattes_k']
    return ''


def conferir_ids_unicos(professores):
    """Para a execução se dois professores ficarem com o mesmo id (nunca deveria acontecer)."""
    vistos = set()
    for professor in professores:
        if professor['id'] in vistos:
            raise ValueError(f"pesquisador_id repetido no cadastro: {professor['id']}")
        vistos.add(professor['id'])
