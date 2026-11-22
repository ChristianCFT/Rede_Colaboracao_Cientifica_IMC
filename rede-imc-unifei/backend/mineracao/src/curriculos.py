"""Etapa 2: percorre o HTML do Lattes de cada professor e despacha cada item para sua dimensão.

Recebe os professores e o índice de identificação; devolve a lista de itens brutos (um por
registro lido nos currículos, ainda com repetições entre coautores).
"""
import html
import re

from bs4 import BeautifulSoup

from configuracao import (BLOCO_ORIENTACOES, BLOCOS_PATENTES, PREFIXO_BANCAS_COMISSOES,
                          PREFIXO_BANCAS_TRABALHOS, SECAO_BANCAS, SECAO_ORIENTACOES,
                          SECAO_PATENTES, SECAO_PRODUCOES, SECAO_PROJETOS, SUBSECOES_ARTIGOS,
                          SUBSECOES_PRODUCAO_TECNICA, TAMANHO_MAXIMO_DO_TEXTO)
from src import dimensoes
from src.identificacao import chaves_do_dono
from src.textos import ler_html, limpar_espacos, normalizar

# O HTML do Lattes é uma lista longa de <div> irmãs: 'title-wrapper' (seção, com um <h1>),
# 'inst_back' (bloco), 'cita-artigos' (subseção) e 'layout-cell-11' (um item). Como a página
# não aninha os itens dentro das seções, o laço guarda em três variáveis "onde estamos".

# Captura o Lattes iD de 16 dígitos no link de um coautor.
LINK_DO_LATTES = re.compile(r'lattes\.cnpq\.br/(\d{16})')
# Captura o prefixo de link no ícone de DOI do item.
LINK_DO_DOI = re.compile(r'^https?://(dx\.)?doi\.org/', re.I)


def extrair_itens(professores, indice):
    """Recebe os professores e o índice e devolve todos os itens lidos dos currículos."""
    itens = []
    for professor in professores:
        if professor['html'] is None:
            continue
        try:
            extrair_curriculo(professor, indice, itens)
        except Exception as erro:  # um currículo problemático não interrompe a execução
            print(f"   aviso: falha ao ler {professor['html'].name}: {erro}")
    return itens


def extrair_curriculo(professor, indice, itens):
    """Lê um currículo e acrescenta à lista 'itens' cada item reconhecido, na ordem do HTML."""
    sopa = BeautifulSoup(ler_html(professor['html']), 'lxml')
    chaves_dono = chaves_do_dono(professor)
    secao = bloco = subsecao = ''
    vistos_por_subtipo = {}
    for elemento in sopa.find_all('div'):
        classes = elemento.get('class') or []
        if 'title-wrapper' in classes:
            h1 = elemento.find('h1')
            secao = limpar_espacos(h1.get_text()) if h1 else ''
            bloco = subsecao = ''
            if secao == SECAO_PROJETOS:
                itens += dimensoes.extrair_projetos(elemento, professor, chaves_dono, indice)
            continue
        if 'inst_back' in classes:
            bloco = limpar_espacos(elemento.get_text())
            subsecao = ''
            continue
        if 'cita-artigos' in classes:
            subsecao = limpar_espacos(elemento.get_text())
            continue
        if 'layout-cell-11' not in classes:
            continue
        dim, subtipo = classificar(secao, bloco, subsecao)
        if not dim:
            continue
        numero = vistos_por_subtipo.get((dim, subtipo), 0) + 1
        vistos_por_subtipo[(dim, subtipo)] = numero
        itens.append(extrair_item(elemento, dim, subtipo, numero, professor, chaves_dono, indice))


def classificar(secao, bloco, subsecao):
    """Recebe onde o item está (seção, bloco, subseção) e devolve (dimensão, subtipo) ou Nones."""
    if secao == SECAO_PRODUCOES and subsecao in SUBSECOES_ARTIGOS:
        return 'ART', SUBSECOES_ARTIGOS[subsecao]
    if secao == SECAO_PRODUCOES and subsecao in SUBSECOES_PRODUCAO_TECNICA:
        return 'PTT', subsecao
    if secao == SECAO_PATENTES and bloco in BLOCOS_PATENTES:
        return 'PTT', 'Patentes e registros - ' + bloco
    if secao == SECAO_ORIENTACOES and bloco == BLOCO_ORIENTACOES:
        return 'ORI', subsecao
    if secao == SECAO_BANCAS and bloco.startswith(PREFIXO_BANCAS_TRABALHOS):
        return 'BAN', 'Trabalho de conclusão - ' + subsecao
    if secao == SECAO_BANCAS and bloco.startswith(PREFIXO_BANCAS_COMISSOES):
        return 'BAN', 'Comissão julgadora - ' + subsecao
    return None, None


def extrair_item(elemento, dim, subtipo, numero, professor, chaves_dono, indice):
    """Recebe a div de um item e devolve o item já com título, ano e participantes."""
    texto, ano_oculto, cvuri, negritos = ler_texto_do_item(elemento)
    links = ler_links_lattes(elemento)
    doi = ler_doi(elemento)
    fonte = f"{professor['id']}|{subtipo}|item {numero}"
    item = dimensoes.novo_item(dim, subtipo, fonte, professor['id'], doi,
                               texto[:TAMANHO_MAXIMO_DO_TEXTO])
    # O nome em negrito no item é sempre o dono do currículo, do jeito que ele assina.
    chaves = chaves_dono | negritos
    if dim == 'ART':
        dimensoes.extrair_artigo(item, texto, cvuri, ano_oculto, links, professor, chaves, indice)
    elif dim == 'PTT':
        dimensoes.extrair_producao_tecnica(item, texto, links, professor, chaves, indice)
    elif dim == 'BAN':
        dimensoes.extrair_banca(item, texto, links, professor, chaves, indice)
    elif dim == 'ORI':
        dimensoes.extrair_orientacao(item, elemento, texto, professor, indice)
    dimensoes.finalizar_item(item, professor)
    return item


def ler_texto_do_item(elemento):
    """Recebe a div do item e devolve (texto visível, ano oculto, cvuri, nomes em negrito)."""
    # Os spans 'informacao-artigo' só servem para o site ordenar a lista e sujariam o texto
    # ('BRAUN, F. 2026 BRAUN, F. ; ...'): o ano é lido deles e depois eles são apagados.
    span_ano = elemento.find('span', attrs={'data-tipo-ordenacao': 'ano'})
    ano_oculto = span_ano.get_text().strip() if span_ano else ''
    citado = elemento.find('span', class_='citado')
    cvuri = html.unescape(citado['cvuri']) if citado and citado.get('cvuri') else ''
    for span in elemento.find_all('span', class_=['informacao-artigo', 'citado']):
        span.decompose()
    for sobrescrito in elemento.find_all('sup'):
        sobrescrito.decompose()
    texto = limpar_espacos(elemento.get_text(' ').replace('\xa0', ' '))
    negritos = set()
    for negrito in elemento.find_all('b'):
        if normalizar(negrito.get_text()):
            negritos.add(normalizar(negrito.get_text()))
    return texto, ano_oculto, cvuri, negritos


def ler_links_lattes(elemento):
    """Recebe a div do item e devolve {nome normalizado: Lattes iD} dos coautores com link."""
    links = {}
    for link in elemento.find_all('a'):
        achado = LINK_DO_LATTES.search(link.get('href') or '')
        if achado and 'tooltip' in (link.get('class') or []):
            links[normalizar(link.get_text())] = achado.group(1)
    return links


def ler_doi(elemento):
    """Recebe a div do item e devolve o DOI do ícone de DOI ('' se não houver)."""
    icone = elemento.find('a', class_='icone-doi')
    if not icone or not icone.get('href'):
        return ''
    return LINK_DO_DOI.sub('', icone['href'].strip()).lower()
