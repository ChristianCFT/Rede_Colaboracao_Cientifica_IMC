# funções de limpeza e normalização de texto
import hashlib
import re
import unicodedata

# 'D' e 'E' também podem ser iniciais
PARTICULAS = {'DE', 'DA', 'DO', 'DAS', 'DOS', 'E', 'D', 'DI', 'DEL', 'VAN', 'VON', 'LA', 'LE', 'Y'}
PARTICULAS_MULTILETRA = {'DE', 'DA', 'DO', 'DAS', 'DOS', 'DI', 'DEL', 'VAN', 'VON', 'LA', 'LE'}

# alguns descompactadores gravam '#U00c1' no lugar de 'Á'
ESCAPE_UNICODE = re.compile(r'#U([0-9a-fA-F]{4})')
NAO_ALFANUMERICO = re.compile(r'[^A-Z0-9]+')
ESPACOS = re.compile(r'\s+')
PREFIXO_DOI = re.compile(r'^(https?://)?(dx\.)?doi\.org/', re.I)
CHARSET_UTF8 = (b'charset=utf-8', b'charset="utf-8"')
TAMANHO_DO_CABECALHO = 4000


def ler_html(caminho):
    with open(caminho, 'rb') as arquivo:
        bruto = arquivo.read()
    cabecalho = bruto[:TAMANHO_DO_CABECALHO].lower()
    # o Lattes salva em Windows-1252, UTF-8 só quando o HTML diz
    if CHARSET_UTF8[0] in cabecalho or CHARSET_UTF8[1] in cabecalho:
        return bruto.decode('utf-8', errors='replace')
    return bruto.decode('cp1252', errors='replace')


def corrigir_escapes(nome):
    return ESCAPE_UNICODE.sub(caractere_do_escape, nome or '')


def caractere_do_escape(achado):
    return chr(int(achado.group(1), 16))


def chave_ordenacao(nome):
    # ordena igual com nome acentuado ou escapado ('Lúcia' / 'L#U00facia')
    chave = ''
    for caractere in corrigir_escapes(nome):
        if ord(caractere) < 128:
            chave += caractere
        else:
            chave += f'#U{ord(caractere):04x}'
    return chave


def tirar_acentos(texto):
    """'Ação' -> 'Acao'"""
    if texto.isascii():
        return texto  # só ASCII
    decomposto = unicodedata.normalize('NFKD', texto)
    return ''.join(letra for letra in decomposto if not unicodedata.combining(letra))


def normalizar(texto):
    if texto is None:
        return ''
    texto = tirar_acentos(str(texto)).upper()
    return NAO_ALFANUMERICO.sub(' ', texto).strip()


def normalizar_sem_particulas(nome):
    """'Ana da Silva' -> 'ANA SILVA'"""
    palavras = []
    for palavra in normalizar(nome).split():
        if palavra not in PARTICULAS:
            palavras.append(palavra)
    return ' '.join(palavras)


def limpar_espacos(texto):
    return ESPACOS.sub(' ', texto or '').strip()


def forma_natural(nome):
    """'SOBRENOME, Nomes' -> 'Nomes SOBRENOME'"""
    if ',' in nome:
        sobrenome, prenomes = nome.split(',', 1)
        return limpar_espacos(prenomes + ' ' + sobrenome)
    return limpar_espacos(nome)


def hash_curto(texto):
    """10 caracteres do SHA-1 (ids PROV-N e EXT-N)"""
    return hashlib.sha1(texto.encode('utf8')).hexdigest()[:10].upper()


def normalizar_doi(doi):
    """tira o prefixo do link e deixa minúsculo"""
    if not doi:
        return ''
    doi = PREFIXO_DOI.sub('', doi.strip()).lower()
    return doi.strip().rstrip('. ')
