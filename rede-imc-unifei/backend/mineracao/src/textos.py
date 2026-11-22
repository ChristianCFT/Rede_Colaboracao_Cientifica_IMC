"""Limpeza e normalização de textos e nomes, usadas por várias etapas.

Recebe textos crus (HTML, índices .txt, nomes de pastas) e devolve versões comparáveis:
sem acento, em maiúsculas, sem pontuação e sem espaços repetidos.
"""
import hashlib
import re
import unicodedata

# Partículas de nomes próprios. 'D' e 'E' também podem ser iniciais de um nome,
# por isso algumas regras usam só as partículas com mais de uma letra.
PARTICULAS = {'DE', 'DA', 'DO', 'DAS', 'DOS', 'E', 'D', 'DI', 'DEL', 'VAN', 'VON', 'LA', 'LE', 'Y'}
PARTICULAS_MULTILETRA = {'DE', 'DA', 'DO', 'DAS', 'DOS', 'DI', 'DEL', 'VAN', 'VON', 'LA', 'LE'}

# Captura o escape '#U00c1' que alguns descompactadores gravam no lugar de 'Á'.
ESCAPE_UNICODE = re.compile(r'#U([0-9a-fA-F]{4})')
# Captura qualquer sequência que não seja letra maiúscula sem acento nem dígito.
NAO_ALFANUMERICO = re.compile(r'[^A-Z0-9]+')
# Captura sequências de espaços, tabulações e quebras de linha.
ESPACOS = re.compile(r'\s+')
# Captura o prefixo de link de um DOI ('https://dx.doi.org/').
PREFIXO_DOI = re.compile(r'^(https?://)?(dx\.)?doi\.org/', re.I)
# Marcas de charset UTF-8 no cabeçalho do HTML.
CHARSET_UTF8 = (b'charset=utf-8', b'charset="utf-8"')
# Só o começo do arquivo é olhado para achar o charset.
TAMANHO_DO_CABECALHO = 4000


def ler_html(caminho):
    """Recebe o caminho de um HTML do Lattes e devolve o texto decodificado."""
    with open(caminho, 'rb') as arquivo:
        bruto = arquivo.read()
    cabecalho = bruto[:TAMANHO_DO_CABECALHO].lower()
    # O Lattes salva em Windows-1252; só usamos UTF-8 quando o próprio HTML diz que é.
    if CHARSET_UTF8[0] in cabecalho or CHARSET_UTF8[1] in cabecalho:
        return bruto.decode('utf-8', errors='replace')
    return bruto.decode('cp1252', errors='replace')


def corrigir_escapes(nome):
    """Recebe um nome de pasta ou arquivo e devolve com '#U00c1' trocado por 'Á'."""
    return ESCAPE_UNICODE.sub(caractere_do_escape, nome or '')


def caractere_do_escape(achado):
    """Recebe um escape '#Uxxxx' achado pela expressão regular e devolve o caractere."""
    return chr(int(achado.group(1), 16))


def chave_ordenacao(nome):
    """Recebe um nome de pasta ou arquivo e devolve a chave usada para ordenar a listagem."""
    # Ordena como se todo caractere não ASCII estivesse escrito '#Uxxxx': assim a ordem é a
    # mesma com nomes acentuados ('Lúcia') ou escapados ('L#U00facia').
    chave = ''
    for caractere in corrigir_escapes(nome):
        if ord(caractere) < 128:
            chave += caractere
        else:
            chave += f'#U{ord(caractere):04x}'
    return chave


def tirar_acentos(texto):
    """Recebe um texto e devolve sem acentos ('Ação' -> 'Acao')."""
    if texto.isascii():
        return texto  # só ASCII: não há acento para tirar (atalho medido no cProfile)
    decomposto = unicodedata.normalize('NFKD', texto)
    return ''.join(letra for letra in decomposto if not unicodedata.combining(letra))


def normalizar(texto):
    """Recebe um texto e devolve maiúsculo, sem acento, só letras e dígitos separados por espaço."""
    if texto is None:
        return ''
    texto = tirar_acentos(str(texto)).upper()
    return NAO_ALFANUMERICO.sub(' ', texto).strip()


def normalizar_sem_particulas(nome):
    """Recebe um nome e devolve normalizado e sem partículas ('Ana da Silva' -> 'ANA SILVA')."""
    palavras = []
    for palavra in normalizar(nome).split():
        if palavra not in PARTICULAS:
            palavras.append(palavra)
    return ' '.join(palavras)


def limpar_espacos(texto):
    """Recebe um texto e devolve com espaços repetidos trocados por um só e sem bordas."""
    return ESPACOS.sub(' ', texto or '').strip()


def forma_natural(nome):
    """Recebe 'SOBRENOME, Nomes' e devolve 'Nomes SOBRENOME' (sem vírgula, só limpa espaços)."""
    if ',' in nome:
        sobrenome, prenomes = nome.split(',', 1)
        return limpar_espacos(prenomes + ' ' + sobrenome)
    return limpar_espacos(nome)


def hash_curto(texto):
    """Recebe um texto e devolve 10 caracteres estáveis do SHA-1 (ids PROV-N e EXT-N)."""
    return hashlib.sha1(texto.encode('utf8')).hexdigest()[:10].upper()


def normalizar_doi(doi):
    """Recebe um DOI como veio do currículo e devolve sem o prefixo de link, em minúsculas."""
    if not doi:
        return ''
    doi = PREFIXO_DOI.sub('', doi.strip()).lower()
    return doi.strip().rstrip('. ')
