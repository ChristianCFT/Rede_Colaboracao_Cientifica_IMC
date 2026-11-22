# lê os índices .txt de cada instituto (nome, Lattes, SIAPE)
import re

from src.textos import chave_ordenacao, normalizar

# registro: texto, nome, lattes, lattes_k, siape, sigla, usado

PREFIXOS_DE_URL = ('http', 'sigaa.', 'www.', 'buscatextual.', 'lattes.')
URL = re.compile(r'https?://\S+')
# 'Nome - http...' ou 'Nome http...'
FIM_DO_NOME = re.compile(r'\s+[-–]\s+|\s+-\s*https?:|\s*https?:')
LATTES_ID = re.compile(r'lattes\.cnpq\.br/(\d{16})')
# id antigo ('K1234567A8')
LATTES_K = re.compile(r'[?&]id=(K\d{4}[A-Z0-9]{5})')
SIAPE = re.compile(r'siape=(\d+)')
SIGLAS_DE_CABECALHO = ('IMC', 'IFQ', 'IRN')


def ler_indices_do_instituto(pasta_instituto, sigla):
    arquivos = [item for item in pasta_instituto.iterdir() if item.name.lower().endswith('.txt')]
    registros = []
    for arquivo in sorted(arquivos, key=chave_do_arquivo):
        registros += ler_indice(arquivo)
    for registro in registros:
        registro['sigla'] = sigla
    return registros


def ler_indice(arquivo):
    # às vezes o nome vem numa linha e os links nas de baixo
    with open(arquivo, encoding='utf-8-sig', errors='replace') as entrada:
        linhas = entrada.read().replace('​', '').splitlines()
    textos = []
    for linha in linhas:
        linha = linha.strip()
        if not linha:
            continue
        if linha.lower().startswith(PREFIXOS_DE_URL):
            if textos:
                textos[-1] += ' ' + linha
            continue
        parece_registro = ' - ' in linha or 'siape=' in linha or 'lattes' in linha.lower()
        if not textos and (not parece_registro or eh_cabecalho(linha)):
            continue
        textos.append(linha)
    return [montar_registro(texto) for texto in textos]


def eh_cabecalho(linha):
    if URL.search(linha):
        return False
    maiusculas = linha.upper()
    return ('INSTITUTO' in maiusculas or 'CAMPUS' in maiusculas
            or normalizar(linha) in SIGLAS_DE_CABECALHO)


def montar_registro(texto):
    lattes = LATTES_ID.findall(texto)
    lattes_k = LATTES_K.findall(texto)
    siape = SIAPE.findall(texto)
    return {'texto': texto, 'nome': FIM_DO_NOME.split(texto)[0].strip(), 'usado': False,
            'lattes': lattes[0] if lattes else '', 'lattes_k': lattes_k[0] if lattes_k else '',
            'siape': siape[0] if siape else ''}


def chave_do_arquivo(caminho):
    return chave_ordenacao(caminho.name)
