"""Etapa 4: junta os registros repetidos (o mesmo artigo no CV de cada coautor) em atividades.

Recebe a lista de itens brutos e devolve a lista de atividades únicas (montadas em
consolidacao.py), cada uma com todos os seus participantes e fontes.
"""
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

# Captura anos e a palavra 'Atual' no período de um projeto ('2019 - Atual').
ANOS_DO_PERIODO = re.compile(r'(\d{4}|Atual)')


def deduplicar(itens):
    """Recebe os itens brutos e devolve as atividades únicas."""
    preparar_itens(itens)
    # Union-find (busca-união): cada item começa no próprio grupo e 'pai' aponta para o
    # representante. Juntar grupos custa quase nada e a ordem das junções não muda o resultado.
    pai = list(range(len(itens)))
    por_dimensao = {}
    for item in itens:
        por_dimensao.setdefault(item['dim'], []).append(item)
    juntar_artigos(por_dimensao.get('ART', []), pai)
    juntar_projetos(por_dimensao.get('PRJ', []), pai)
    juntar_orientacoes(por_dimensao.get('ORI', []), pai)
    juntar_bancas(por_dimensao.get('BAN', []), pai)
    juntar_producao_tecnica(por_dimensao.get('PTT', []), pai)
    # O mesmo texto duas vezes no mesmo currículo é a mesma atividade.
    repetidos = {}
    for item in itens:
        chave = (item['dono'], item['dim'], normalizar(item['texto']))
        repetidos.setdefault(chave, []).append(item)
    for grupo in repetidos.values():
        juntar_todos(grupo, pai)
    # Cada grupo fica com seus itens em ordem de leitura; os grupos, na ordem do primeiro item.
    grupos = {}
    for item in itens:
        grupos.setdefault(encontrar(pai, item['posicao']), []).append(item)
    return consolidar(list(grupos.values()))


def preparar_itens(itens):
    """Numera os itens (posição no union-find), limpa títulos e normaliza DOI e título."""
    for posicao, item in enumerate(itens):
        item['posicao'] = posicao
        if item['titulo'] and item['titulo'] == item['ano']:
            item['titulo'] = ''
        item['titulo'] = item['titulo'].strip()
        if item['doi']:
            item['doi'] = normalizar_doi(item['doi'])
        # Normalizado uma vez aqui, em vez de a cada comparação (otimização medida no cProfile).
        item['titulo_normalizado'] = normalizar(item['titulo'])


def encontrar(pai, posicao):
    """Recebe a posição de um item e devolve o representante do seu grupo."""
    while pai[posicao] != posicao:
        pai[posicao] = pai[pai[posicao]]  # encurta o caminho para as próximas buscas
        posicao = pai[posicao]
    return posicao


def unir(pai, a, b):
    """Junta os grupos de a e b; o representante é sempre o menor índice (resultado estável)."""
    raiz_a, raiz_b = encontrar(pai, a), encontrar(pai, b)
    if raiz_a != raiz_b:
        pai[max(raiz_a, raiz_b)] = min(raiz_a, raiz_b)


def juntar_todos(grupo, pai):
    """Junta todos os itens do grupo ao primeiro."""
    for item in grupo[1:]:
        unir(pai, grupo[0]['posicao'], item['posicao'])


def comparar_pares(grupo, pai, mesma_atividade):
    """Compara cada par do grupo com a regra da dimensão e junta os que são a mesma atividade."""
    for i in range(len(grupo)):
        for j in range(i + 1, len(grupo)):
            if mesma_atividade(grupo[i], grupo[j]):
                unir(pai, grupo[i]['posicao'], grupo[j]['posicao'])


def agrupar_por_campo(itens, campo):
    """Agrupa os itens pelo valor de um campo, ignorando valores vazios."""
    grupos = {}
    for item in itens:
        if item[campo]:
            grupos.setdefault(item[campo], []).append(item)
    return grupos


def agrupar(itens, calcular_chave):
    """Agrupa os itens pela chave calculada; itens sem chave ficam de fora."""
    grupos = {}
    for item in itens:
        chave = calcular_chave(item)
        if chave:
            grupos.setdefault(chave, []).append(item)
    return grupos


# ------------------------------------------------------------------- artigos (ART)
def juntar_artigos(itens, pai):
    """ART: mesmo DOI; depois título e ano com as regras de mesmo_artigo."""
    for grupo in agrupar_por_campo(itens, 'doi').values():
        juntar_todos(grupo, pai)
    for grupo in agrupar(itens, chave_titulo_e_ano).values():
        comparar_pares(grupo, pai, mesmo_artigo)


def chave_titulo_e_ano(item):
    """Começo do título normalizado + ano (só compara registros que podem ser o mesmo)."""
    if not item['titulo_normalizado'] or not item['ano']:
        return None
    return item['titulo_normalizado'][:PREFIXO_DO_TITULO] + '|' + item['ano']


def mesmo_artigo(a, b):
    """Título idêntico junta; título só parecido exige participante e números em comum."""
    if dois_diferentes(a, b, 'doi'):
        return False
    if a['dono'] == b['dono'] and a['subtipo'] != b['subtipo']:
        return False  # o mesmo autor registrou a versão em anais e a em periódico: são duas
    titulo_a, titulo_b = a['titulo_normalizado'], b['titulo_normalizado']
    if titulo_a == titulo_b:
        longo = len(titulo_a.split()) >= MIN_PALAVRAS_TITULO_IDENTICO
        return longo or ligados(a, b) or a['dono'] == b['dono']
    if a['dono'] == b['dono'] or len(titulo_a.split()) < MIN_PALAVRAS_TITULO_SEMELHANTE:
        return False
    if semelhanca(titulo_a, titulo_b) < TITULO_QUASE_IDENTICO:
        return False
    # 'Parte I' e 'Parte II' têm títulos quase iguais, mas nunca são o mesmo artigo.
    mesmos_numeros = numeros_do_titulo(titulo_a) == numeros_do_titulo(titulo_b)
    return evidencia_de_participantes(a, b) and mesmos_numeros


# ------------------------------------------------------------------- produção técnica (PTT)
def juntar_producao_tecnica(itens, pai):
    """PTT: mesmo número de registro, mesmo DOI; depois tipo, título e ano."""
    for campo in ('registro', 'doi'):
        for grupo in agrupar_por_campo(itens, campo).values():
            juntar_todos(grupo, pai)
    for grupo in agrupar(itens, chave_tipo_titulo_e_ano).values():
        comparar_pares(grupo, pai, mesma_producao_tecnica)


def chave_tipo_titulo_e_ano(item):
    """Subtipo + começo do título normalizado + ano."""
    if not item['titulo_normalizado'] or not item['ano']:
        return None
    inicio = item['titulo_normalizado'][:PREFIXO_DO_TITULO]
    return item['subtipo'] + '|' + inicio + '|' + item['ano']


def mesma_producao_tecnica(a, b):
    """No mesmo CV só junta mesmo título e mesmos participantes; entre CVs, como nos artigos."""
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


# ------------------------------------------------------------------- projetos (PRJ)
def juntar_projetos(itens, pai):
    """PRJ: título igual ou quase igual, períodos que se sobrepõem e integrante em comum."""
    for grupo in agrupar(itens, chave_inicio_do_titulo).values():
        comparar_pares(grupo, pai, mesmo_projeto)


def chave_inicio_do_titulo(item):
    """Começo do título normalizado (projetos não têm um ano único para agrupar)."""
    return item['titulo_normalizado'][:PREFIXO_DO_TITULO]


def mesmo_projeto(a, b):
    """Exige integrante em comum (ou mesmo CV) para não unir projetos de títulos genéricos."""
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
    """Recebe o projeto e devolve (ano de início, ano de fim); 'Atual' vira o ano atual."""
    anos = ANOS_DO_PERIODO.findall(item['periodo'])
    inicio = int(anos[0]) if anos and anos[0].isdigit() else int(item['ano'] or 0)
    fim = anos[1] if len(anos) > 1 else (anos[0] if anos else item['ano'])
    if fim == 'Atual':
        return inicio, ANO_ATUAL_DOS_PROJETOS
    return inicio, int(fim or inicio)


# ------------------------------------------------------------------- orientações e bancas
def juntar_orientacoes(itens, pai):
    """ORI: mesmo aluno, ano e tipo, com título semelhante."""
    for grupo in agrupar(itens, chave_aluno_ano_e_tipo).values():
        comparar_pares(grupo, pai, mesma_orientacao)


def chave_aluno_ano_e_tipo(item):
    """Aluno normalizado + ano + subtipo (sem aluno não há como agrupar)."""
    aluno = normalizar(item['aluno'])
    return (aluno + '|' + item['ano'] + '|' + item['subtipo']) if aluno else None


def mesma_orientacao(a, b):
    """Entre CVs basta 0,6 (orientador e coorientador registram a mesma); no mesmo CV, 0,9."""
    limiar = SIMILARIDADE_ORIENTACAO_ENTRE_CVS
    if a['dono'] == b['dono']:
        limiar = SIMILARIDADE_ORIENTACAO_MESMO_CV
    return semelhanca_ou_vazio(a, b) >= limiar


def juntar_bancas(itens, pai):
    """BAN: trabalhos pelo candidato; comissões pela descrição com evidência de membros."""
    for chave, grupo in agrupar(itens, chave_da_banca).items():
        if chave.startswith('C|'):
            comparar_pares(grupo, pai, mesma_banca_de_trabalho)
        else:
            comparar_pares(grupo, pai, mesma_comissao)
    # Depois, o mesmo trabalho com o nome do candidato escrito diferente em cada CV.
    for grupo in agrupar(itens, chave_primeiro_nome_ano_e_tipo).values():
        comparar_pares(grupo, pai, mesma_banca_com_candidato_diferente)


def chave_da_banca(item):
    """Trabalho com candidato de 2+ palavras: 'C|candidato|ano|tipo'; senão 'T|título|ano|tipo'."""
    # Chave de citação: sem partículas e com 'JR' = 'JUNIOR' ('Joel Faria Jr' = 'Joel Faria Junior').
    candidato = chave_citacao(item['candidato'])
    if item['subtipo'].startswith('Trabalho') and len(candidato.split()) >= 2:
        return 'C|' + candidato + '|' + item['ano'] + '|' + item['subtipo']
    if not item['titulo_normalizado']:
        return None
    return 'T|' + item['titulo_normalizado'] + '|' + item['ano'] + '|' + item['subtipo']


def mesma_banca_de_trabalho(a, b):
    """Entre CVs basta 0,5 de semelhança no título; no mesmo CV, 0,9."""
    limiar = SIMILARIDADE_BANCA_ENTRE_CVS
    if a['dono'] == b['dono']:
        limiar = SIMILARIDADE_BANCA_MESMO_CV
    return semelhanca_ou_vazio(a, b) >= limiar


def mesma_comissao(a, b):
    """Descrições de comissão se repetem: entre CVs, o dono de um precisa aparecer no outro."""
    if a['dono'] == b['dono']:
        return membros(a) == membros(b)
    return ligados(a, b)


def chave_primeiro_nome_ano_e_tipo(item):
    """Trabalho de conclusão: primeiro nome do candidato + ano + tipo (sem candidato, sem chave)."""
    nome = normalizar(item['candidato']).split()
    if not item['subtipo'].startswith('Trabalho') or not nome:
        return None
    return nome[0] + '|' + item['ano'] + '|' + item['subtipo']


def mesma_banca_com_candidato_diferente(a, b):
    """CVs diferentes, um dono aparece no outro, candidatos parecidos e título bem parecido."""
    # Pega erros de digitação e abreviações no nome do aluno ('Rezende' x 'Resende',
    # 'Mariana de F. Matos' x 'Mariana de Freitas Matos'), que mudam a chave do candidato.
    if a['dono'] == b['dono'] or not a['titulo_normalizado'] or not b['titulo_normalizado']:
        return False
    if len(palavras_do_nome(a['candidato']) & palavras_do_nome(b['candidato'])) < PALAVRAS_EM_COMUM_DO_CANDIDATO:
        return False
    if not ligados(a, b):
        return False
    return semelhanca(a['titulo_normalizado'], b['titulo_normalizado']) >= SIMILARIDADE_BANCA_CANDIDATO_DIFERENTE


def palavras_do_nome(nome):
    """Recebe um nome e devolve o conjunto das suas palavras, sem acento e sem partículas."""
    return set(normalizar_sem_particulas(nome).split())
