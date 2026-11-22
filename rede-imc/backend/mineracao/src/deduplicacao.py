# etapa 4: junta os registros repetidos (mesmo artigo no CV de cada coautor)
import re

from configuracao import (ANO_ATUAL_DOS_PROJETOS, MIN_PALAVRAS_TITULO_IDENTICO,
                          MIN_PALAVRAS_TITULO_SEMELHANTE, PALAVRAS_EM_COMUM_DO_CANDIDATO,
                          PREFIXO_DO_TITULO, SIMILARIDADE_BANCA_CANDIDATO_DIFERENTE,
                          SIMILARIDADE_BANCA_ENTRE_CVS, SIMILARIDADE_BANCA_MESMO_CV,
                          SIMILARIDADE_ORIENTACAO_ENTRE_CVS, SIMILARIDADE_ORIENTACAO_MESMO_CV,
                          TITULO_QUASE_IDENTICO)
from src.consolidacao import consolidar
from src.evidencias import (dois_diferentes, evidencia_de_participantes, ligados, membros,
                            numeros_do_titulo, semelhanca, semelhanca_ou_vazio)
from src.identificacao import chave_citacao
from src.textos import normalizar, normalizar_doi, normalizar_sem_particulas

# ex: '2019 - Atual'
ANOS_DO_PERIODO = re.compile(r'(\d{4}|Atual)')


def deduplicar(itens):
    preparar_itens(itens)
    # union-find
    pai = list(range(len(itens)))
    por_dimensao = {}
    for item in itens:
        por_dimensao.setdefault(item['dim'], []).append(item)
    juntar_artigos(por_dimensao.get('ART', []), pai)
    juntar_projetos(por_dimensao.get('PRJ', []), pai)
    juntar_orientacoes(por_dimensao.get('ORI', []), pai)
    juntar_bancas(por_dimensao.get('BAN', []), pai)
    juntar_producao_tecnica(por_dimensao.get('PTT', []), pai)
    # mesmo texto no mesmo currículo = mesma atividade
    repetidos = {}
    for item in itens:
        chave = (item['dono'], item['dim'], normalizar(item['texto']))
        repetidos.setdefault(chave, []).append(item)
    for grupo in repetidos.values():
        juntar_todos(grupo, pai)
    grupos = {}
    for item in itens:
        grupos.setdefault(encontrar(pai, item['posicao']), []).append(item)
    return consolidar(list(grupos.values()))


def preparar_itens(itens):
    for posicao, item in enumerate(itens):
        item['posicao'] = posicao
        if item['titulo'] and item['titulo'] == item['ano']:
            item['titulo'] = ''
        item['titulo'] = item['titulo'].strip()
        if item['doi']:
            item['doi'] = normalizar_doi(item['doi'])
        # normaliza uma vez só aqui
        item['titulo_normalizado'] = normalizar(item['titulo'])


def encontrar(pai, posicao):
    while pai[posicao] != posicao:
        pai[posicao] = pai[pai[posicao]]  # compressão de caminho
        posicao = pai[posicao]
    return posicao


def unir(pai, a, b):
    """o representante é sempre o menor índice"""
    raiz_a, raiz_b = encontrar(pai, a), encontrar(pai, b)
    if raiz_a != raiz_b:
        pai[max(raiz_a, raiz_b)] = min(raiz_a, raiz_b)


def juntar_todos(grupo, pai):
    for item in grupo[1:]:
        unir(pai, grupo[0]['posicao'], item['posicao'])


def comparar_pares(grupo, pai, mesma_atividade):
    for i in range(len(grupo)):
        for j in range(i + 1, len(grupo)):
            if mesma_atividade(grupo[i], grupo[j]):
                unir(pai, grupo[i]['posicao'], grupo[j]['posicao'])


def agrupar_por_campo(itens, campo):
    grupos = {}
    for item in itens:
        if item[campo]:
            grupos.setdefault(item[campo], []).append(item)
    return grupos


def agrupar(itens, calcular_chave):
    grupos = {}
    for item in itens:
        chave = calcular_chave(item)
        if chave:
            grupos.setdefault(chave, []).append(item)
    return grupos


# artigos
def juntar_artigos(itens, pai):
    for grupo in agrupar_por_campo(itens, 'doi').values():
        juntar_todos(grupo, pai)
    for grupo in agrupar(itens, chave_titulo_e_ano).values():
        comparar_pares(grupo, pai, mesmo_artigo)


def chave_titulo_e_ano(item):
    if not item['titulo_normalizado'] or not item['ano']:
        return None
    return item['titulo_normalizado'][:PREFIXO_DO_TITULO] + '|' + item['ano']


def mesmo_artigo(a, b):
    """título igual junta; parecido precisa de participante e números em comum"""
    if dois_diferentes(a, b, 'doi'):
        return False
    if a['dono'] == b['dono'] and a['subtipo'] != b['subtipo']:
        return False  # mesmo autor com versão em anais e em periódico
    titulo_a, titulo_b = a['titulo_normalizado'], b['titulo_normalizado']
    if titulo_a == titulo_b:
        longo = len(titulo_a.split()) >= MIN_PALAVRAS_TITULO_IDENTICO
        return longo or ligados(a, b) or a['dono'] == b['dono']
    if a['dono'] == b['dono'] or len(titulo_a.split()) < MIN_PALAVRAS_TITULO_SEMELHANTE:
        return False
    if semelhanca(titulo_a, titulo_b) < TITULO_QUASE_IDENTICO:
        return False
    # 'Parte I' e 'Parte II' não são o mesmo artigo
    mesmos_numeros = numeros_do_titulo(titulo_a) == numeros_do_titulo(titulo_b)
    return evidencia_de_participantes(a, b) and mesmos_numeros


# produção técnica
def juntar_producao_tecnica(itens, pai):
    for campo in ('registro', 'doi'):
        for grupo in agrupar_por_campo(itens, campo).values():
            juntar_todos(grupo, pai)
    for grupo in agrupar(itens, chave_tipo_titulo_e_ano).values():
        comparar_pares(grupo, pai, mesma_producao_tecnica)


def chave_tipo_titulo_e_ano(item):
    if not item['titulo_normalizado'] or not item['ano']:
        return None
    inicio = item['titulo_normalizado'][:PREFIXO_DO_TITULO]
    return item['subtipo'] + '|' + inicio + '|' + item['ano']


def mesma_producao_tecnica(a, b):
    """no mesmo CV só junta se título e participantes forem iguais"""
    if dois_diferentes(a, b, 'registro') or dois_diferentes(a, b, 'doi'):
        return False
    titulo_a, titulo_b = a['titulo_normalizado'], b['titulo_normalizado']
    if a['dono'] == b['dono']:
        return titulo_a == titulo_b and membros(a) == membros(b)
    if titulo_a == titulo_b:
        return len(titulo_a.split()) >= MIN_PALAVRAS_TITULO_IDENTICO or ligados(a, b)
    if len(titulo_a.split()) < MIN_PALAVRAS_TITULO_SEMELHANTE:
        return False
    if semelhanca(titulo_a, titulo_b) < TITULO_QUASE_IDENTICO:
        return False
    mesmos_numeros = numeros_do_titulo(titulo_a) == numeros_do_titulo(titulo_b)
    return evidencia_de_participantes(a, b) and mesmos_numeros


# projetos
def juntar_projetos(itens, pai):
    for grupo in agrupar(itens, chave_inicio_do_titulo).values():
        comparar_pares(grupo, pai, mesmo_projeto)


def chave_inicio_do_titulo(item):
    return item['titulo_normalizado'][:PREFIXO_DO_TITULO]


def mesmo_projeto(a, b):
    """precisa de integrante em comum (tem muito título genérico)"""
    inicio_a, fim_a = periodo_do_projeto(a)
    inicio_b, fim_b = periodo_do_projeto(b)
    if not (inicio_a <= fim_b and inicio_b <= fim_a):
        return False
    titulo_a, titulo_b = a['titulo_normalizado'], b['titulo_normalizado']
    if titulo_a != titulo_b:
        if len(titulo_a.split()) < MIN_PALAVRAS_TITULO_SEMELHANTE:
            return False
        if semelhanca(titulo_a, titulo_b) < TITULO_QUASE_IDENTICO:
            return False
    return a['dono'] == b['dono'] or evidencia_de_participantes(a, b)


def periodo_do_projeto(item):
    """(início, fim); 'Atual' vira o ano atual"""
    anos = ANOS_DO_PERIODO.findall(item['periodo'])
    inicio = int(anos[0]) if anos and anos[0].isdigit() else int(item['ano'] or 0)
    fim = anos[1] if len(anos) > 1 else (anos[0] if anos else item['ano'])
    if fim == 'Atual':
        return inicio, ANO_ATUAL_DOS_PROJETOS
    return inicio, int(fim or inicio)


# orientações e bancas
def juntar_orientacoes(itens, pai):
    for grupo in agrupar(itens, chave_aluno_ano_e_tipo).values():
        comparar_pares(grupo, pai, mesma_orientacao)


def chave_aluno_ano_e_tipo(item):
    aluno = normalizar(item['aluno'])
    return (aluno + '|' + item['ano'] + '|' + item['subtipo']) if aluno else None


def mesma_orientacao(a, b):
    """entre CVs 0.6 (orientador e coorientador registram a mesma), no mesmo CV 0.9"""
    limiar = SIMILARIDADE_ORIENTACAO_ENTRE_CVS
    if a['dono'] == b['dono']:
        limiar = SIMILARIDADE_ORIENTACAO_MESMO_CV
    return semelhanca_ou_vazio(a, b) >= limiar


def juntar_bancas(itens, pai):
    for chave, grupo in agrupar(itens, chave_da_banca).items():
        if chave.startswith('C|'):
            comparar_pares(grupo, pai, mesma_banca_de_trabalho)
        else:
            comparar_pares(grupo, pai, mesma_comissao)
    # mesmo trabalho com o nome do candidato escrito diferente
    for grupo in agrupar(itens, chave_primeiro_nome_ano_e_tipo).values():
        comparar_pares(grupo, pai, mesma_banca_com_candidato_diferente)


def chave_da_banca(item):
    """'C|candidato|ano|tipo' ou 'T|título|ano|tipo'"""
    # 'Joel Faria Jr' = 'Joel Faria Junior'
    candidato = chave_citacao(item['candidato'])
    if item['subtipo'].startswith('Trabalho') and len(candidato.split()) >= 2:
        return 'C|' + candidato + '|' + item['ano'] + '|' + item['subtipo']
    if not item['titulo_normalizado']:
        return None
    return 'T|' + item['titulo_normalizado'] + '|' + item['ano'] + '|' + item['subtipo']


def mesma_banca_de_trabalho(a, b):
    limiar = SIMILARIDADE_BANCA_ENTRE_CVS
    if a['dono'] == b['dono']:
        limiar = SIMILARIDADE_BANCA_MESMO_CV
    return semelhanca_ou_vazio(a, b) >= limiar


def mesma_comissao(a, b):
    """comissão se repete muito: o dono de um tem que aparecer no outro"""
    if a['dono'] == b['dono']:
        return membros(a) == membros(b)
    return ligados(a, b)


def chave_primeiro_nome_ano_e_tipo(item):
    nome = normalizar(item['candidato']).split()
    if not item['subtipo'].startswith('Trabalho') or not nome:
        return None
    return nome[0] + '|' + item['ano'] + '|' + item['subtipo']


def mesma_banca_com_candidato_diferente(a, b):
    # pega erro de digitação no nome ('Rezende' x 'Resende', 'F.' x 'Freitas')
    if a['dono'] == b['dono'] or not a['titulo_normalizado'] or not b['titulo_normalizado']:
        return False
    if len(palavras_do_nome(a['candidato']) & palavras_do_nome(b['candidato'])) < PALAVRAS_EM_COMUM_DO_CANDIDATO:
        return False
    if not ligados(a, b):
        return False
    return semelhanca(a['titulo_normalizado'], b['titulo_normalizado']) >= SIMILARIDADE_BANCA_CANDIDATO_DIFERENTE


def palavras_do_nome(nome):
    return set(normalizar_sem_particulas(nome).split())
