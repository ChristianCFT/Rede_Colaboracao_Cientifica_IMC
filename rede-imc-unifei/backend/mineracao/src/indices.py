"""Etapa 1 (índices): lê os arquivos .txt de cada instituto, com nome, Lattes e SIAPE.

Recebe a pasta de um instituto e devolve um registro por professor listado nos seus índices.
"""
import re

from src.textos import chave_ordenacao, normalizar

# Cada registro é um dicionário com as chaves: texto (o registro inteiro, com os links),
# nome, lattes, lattes_k (id antigo 'K...'), siape, sigla e usado (já casou com uma pasta?).

# Linhas do índice que continuam o registro anterior (só trazem links).
PREFIXOS_DE_URL = ('http', 'sigaa.', 'www.', 'buscatextual.', 'lattes.')
# Captura qualquer endereço http(s).
URL = re.compile(r'https?://\S+')
# Captura onde termina o nome no registro do índice ('Nome - http...' ou 'Nome http...').
FIM_DO_NOME = re.compile(r'\s+[-–]\s+|\s+-\s*https?:|\s*https?:')
# Captura o Lattes iD de 16 dígitos de um link do Lattes.
LATTES_ID = re.compile(r'lattes\.cnpq\.br/(\d{16})')
# Captura o id antigo do Lattes ('K1234567A8') de um link do buscatextual.
LATTES_K = re.compile(r'[?&]id=(K\d{4}[A-Z0-9]{5})')
# Captura o número SIAPE do link do SIGAA.
SIAPE = re.compile(r'siape=(\d+)')
# Siglas que aparecem sozinhas como cabeçalho de alguns índices.
SIGLAS_DE_CABECALHO = ('IMC', 'IFQ', 'IRN')


def ler_indices_do_instituto(pasta_instituto, sigla):
    """Recebe a pasta de um instituto e devolve os registros de todos os seus índices .txt."""
    arquivos = [item for item in pasta_instituto.iterdir() if item.name.lower().endswith('.txt')]
    registros = []
    for arquivo in sorted(arquivos, key=chave_do_arquivo):
        registros += ler_indice(arquivo)
    for registro in registros:
        registro['sigla'] = sigla
    return registros


def ler_indice(arquivo):
    """Recebe um índice .txt e devolve um registro (nome, Lattes, SIAPE, texto) por professor."""
    # Os índices variam: às vezes nome e links na mesma linha, às vezes o nome numa linha e os
    # links nas seguintes. Um registro começa numa linha que não é link; links são anexados.
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
    """Recebe a primeira linha útil do índice e diz se ela é o nome do instituto."""
    if URL.search(linha):
        return False
    maiusculas = linha.upper()
    return ('INSTITUTO' in maiusculas or 'CAMPUS' in maiusculas
            or normalizar(linha) in SIGLAS_DE_CABECALHO)


def montar_registro(texto):
    """Recebe o texto de um registro do índice e devolve nome, Lattes, Lattes antigo e SIAPE."""
    lattes = LATTES_ID.findall(texto)
    lattes_k = LATTES_K.findall(texto)
    siape = SIAPE.findall(texto)
    return {'texto': texto, 'nome': FIM_DO_NOME.split(texto)[0].strip(), 'usado': False,
            'lattes': lattes[0] if lattes else '', 'lattes_k': lattes_k[0] if lattes_k else '',
            'siape': siape[0] if siape else ''}


def chave_do_arquivo(caminho):
    """Recebe o caminho de um índice e devolve a chave de ordenação do seu nome."""
    return chave_ordenacao(caminho.name)
