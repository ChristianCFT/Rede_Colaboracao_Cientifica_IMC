# etapa 6: gera os CSVs (UTF-8 com BOM pro Excel abrir os acentos)
import csv
import json

from configuracao import CAMADA, COLUNA_DA_DIMENSAO, DIMENSOES, NOME_DA_DIMENSAO
from src.rede import tipo_de_relacao, vetor_bruto
from src.textos import normalizar

COLUNAS_COMPLETO = ['pesquisador_id', 'nome', 'instituto', 'area', 'ciape', 'lattes_url']
COLUNAS_ENTRADA = (['nome do pesquisador', 'instituto', 'area de trabalho']
                   + [COLUNA_DA_DIMENSAO[dim] for dim in DIMENSOES]
                   + ['pesquisador_id', 'vetor contagem', 'observacao'])
COLUNAS_SAIDA = ['nome do pesquisador 1', 'nome do pesquisador 2', 'instituto pesquisador 1',
                 'instituto pesquisador 2', 'area de trabalho pesquisador 1',
                 'area de trabalho pesquisador 2', 'vetor bruto', 'id pesquisador 1',
                 'id pesquisador 2', 'tipo de relacao', 'vetor contagem']
COLUNAS_ATIVIDADES = ['id_atividade', 'dimensao', 'posicao_no_vetor', 'tipo_atividade', 'subtipo',
                      'titulo', 'ano', 'doi', 'numero_registro', 'aluno_ou_candidato',
                      'periodo_projeto', 'situacao_projeto', 'ids_participantes',
                      'nomes_participantes', 'institutos_participantes', 'papeis_participantes',
                      'metodo_identificacao', f'ids_participantes_{CAMADA}',
                      'qtd_participantes_identificados', f'qtd_participantes_{CAMADA}',
                      f'envolve_{CAMADA}', 'nomes_nao_resolvidos', 'registrado_no_cv_de',
                      'qtd_registros_unificados', 'fontes', 'chave_deduplicacao']
OBSERVACAO_EXTERNO = ('pesquisador externo: sem currículo no zip; '
                      'características individuais não determináveis')
OBSERVACAO_SEM_CV = ('sem currículo Lattes no zip; características individuais não determináveis '
                     '(aparece em {} atividade(s) registradas por outros professores)')


def gravar_csvs(pasta, professores, externos, rede):
    pessoas = {'professores': {professor['id']: professor for professor in professores},
               'externos': externos}
    pasta.mkdir(parents=True, exist_ok=True)
    gravar_csv(pasta / 'dataset_completo_UNIFEI.csv', COLUNAS_COMPLETO,
               linhas_completo(professores))
    gravar_csv(pasta / f'dataset_entrada_{CAMADA}.csv', COLUNAS_ENTRADA,
               linhas_entrada(rede, pessoas))
    gravar_csv(pasta / f'dataset_saida_{CAMADA}.csv', COLUNAS_SAIDA, linhas_saida(rede, pessoas))
    gravar_csv(pasta / f'dataset_atividades_{CAMADA}.csv', COLUNAS_ATIVIDADES,
               linhas_atividades(rede, pessoas))


def gravar_csv(caminho, colunas, linhas):
    with open(caminho, 'w', encoding='utf-8-sig', newline='') as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=colunas, quoting=csv.QUOTE_MINIMAL)
        escritor.writeheader()
        escritor.writerows(linhas)


def em_json(valor):
    return json.dumps(valor, ensure_ascii=False)


def nome_de(pessoa, pessoas):
    """nome do professor ou o nome mais visto do externo"""
    if pessoa.startswith('EXT-'):
        externo = pessoas['externos'].get(pessoa)
        return externo['nomes'].most_common(1)[0][0] if externo else pessoa
    return pessoas['professores'][pessoa]['nome']


def instituto_de(pessoa, pessoas):
    if pessoa.startswith('EXT-'):
        return 'EXT'
    return pessoas['professores'][pessoa]['instituto']


def area_de(pessoa, pessoas):
    if pessoa.startswith('EXT-'):
        return ''
    return pessoas['professores'][pessoa]['area']


def linhas_completo(professores):
    decorados = []
    for ordem, professor in enumerate(professores):
        decorados.append((professor['instituto'], normalizar(professor['nome']), ordem, professor))
    decorados.sort()  # 'ordem' desempata
    linhas = []
    for _, _, _, professor in decorados:
        linhas.append({'pesquisador_id': professor['id'], 'nome': professor['nome'],
                       'instituto': professor['instituto'], 'area': professor['area'],
                       'ciape': professor['siape'], 'lattes_url': professor['url_lattes']})
    return linhas


def linhas_entrada(rede, pessoas):
    individuais = atividades_individuais(rede)
    com_relacao = {pessoa for pessoa, _ in rede['pares']}
    linhas = []
    for pessoa in rede['membros'] + rede['outros'] + rede['externos']:
        linha = {'nome do pesquisador': nome_de(pessoa, pessoas),
                 'instituto': instituto_de(pessoa, pessoas),
                 'area de trabalho': area_de(pessoa, pessoas), 'pesquisador_id': pessoa}
        observacoes = preencher_atividades(linha, pessoa, individuais, pessoas)
        if not pessoa.startswith('EXT-') and not pessoas['professores'][pessoa]['area']:
            observacoes.append('área de atuação ausente na fonte')
        if pessoa in rede['membros'] and pessoa not in com_relacao:
            observacoes.append(f'professor do {CAMADA} sem relação identificada')
        linha['observacao'] = '; '.join(observacoes)
        linhas.append(linha)
    return linhas


def atividades_individuais(rede):
    professores_da_rede = set(rede['membros']) | set(rede['outros'])
    individuais = {}
    for atividade in rede['selecionadas']:
        for pessoa in atividade['participantes']:
            if pessoa not in professores_da_rede:
                continue
            if pessoa not in individuais:
                individuais[pessoa] = {dim: [] for dim in DIMENSOES}
            individuais[pessoa][atividade['dim']].append(atividade['codigo'])
    return individuais


def preencher_atividades(linha, pessoa, individuais, pessoas):
    """sem currículo as colunas ficam vazias (nunca zero)"""
    if pessoa.startswith('EXT-'):
        deixar_vazias(linha)
        return [OBSERVACAO_EXTERNO]
    minhas = individuais.get(pessoa, {dim: [] for dim in DIMENSOES})
    if pessoas['professores'][pessoa]['html'] is None:
        deixar_vazias(linha)
        quantidade = sum(len(codigos) for codigos in minhas.values())
        return [OBSERVACAO_SEM_CV.format(quantidade)]
    for dim in DIMENSOES:
        linha[COLUNA_DA_DIMENSAO[dim]] = em_json(sorted(minhas[dim]))
    linha['vetor contagem'] = em_json([len(minhas[dim]) for dim in DIMENSOES])
    return []


def deixar_vazias(linha):
    for dim in DIMENSOES:
        linha[COLUNA_DA_DIMENSAO[dim]] = ''
    linha['vetor contagem'] = ''


def linhas_saida(rede, pessoas):
    linhas = []
    for (pessoa, parceiro), por_dimensao in pares_ordenados(rede, pessoas):
        vetor = vetor_bruto(por_dimensao)
        instituto_parceiro = instituto_de(parceiro, pessoas)
        linhas.append({
            'nome do pesquisador 1': nome_de(pessoa, pessoas),
            'nome do pesquisador 2': nome_de(parceiro, pessoas),
            'instituto pesquisador 1': instituto_de(pessoa, pessoas),
            'instituto pesquisador 2': instituto_parceiro,
            'area de trabalho pesquisador 1': area_de(pessoa, pessoas),
            'area de trabalho pesquisador 2': area_de(parceiro, pessoas),
            'vetor bruto': em_json(vetor), 'id pesquisador 1': pessoa, 'id pesquisador 2': parceiro,
            'tipo de relacao': tipo_de_relacao(parceiro, rede, instituto_parceiro),
            'vetor contagem': em_json([len(codigos) for codigos in vetor]),
        })
    return linhas


def pares_ordenados(rede, pessoas):
    """por nome do pesquisador 1, depois camada, outros e externos"""
    decorados = []
    for ordem, (par, por_dimensao) in enumerate(rede['pares'].items()):
        pessoa, parceiro = par
        grupo = 0 if parceiro in rede['membros'] else (2 if parceiro.startswith('EXT') else 1)
        nome_1 = normalizar(nome_de(pessoa, pessoas))
        nome_2 = normalizar(nome_de(parceiro, pessoas))
        decorados.append(((nome_1, grupo, nome_2, ordem), par, por_dimensao))
    decorados.sort()  # nunca empata
    return [(par, por_dimensao) for _, par, por_dimensao in decorados]


def linhas_atividades(rede, pessoas):
    membros = set(rede['membros'])
    linhas = []
    for atividade in rede['selecionadas']:
        ids = list(atividade['participantes'])
        do_imc = [pessoa for pessoa in ids if pessoa in membros]
        linha = dados_da_atividade(atividade)
        linha.update({
            'ids_participantes': ';'.join(ids),
            'nomes_participantes': ';'.join(nome_de(pessoa, pessoas) for pessoa in ids),
            'institutos_participantes': ';'.join(instituto_de(pessoa, pessoas) for pessoa in ids),
            'papeis_participantes': juntar_conjuntos(atividade, ids, 'papeis'),
            'metodo_identificacao': juntar_conjuntos(atividade, ids, 'metodos'),
            f'ids_participantes_{CAMADA}': ';'.join(do_imc),
            'qtd_participantes_identificados': len(ids),
            f'qtd_participantes_{CAMADA}': len(do_imc),
            f'envolve_{CAMADA}': 'sim' if do_imc else 'não',
        })
        linhas.append(linha)
    return linhas


def dados_da_atividade(atividade):
    nao_resolvidos = []
    for nao_resolvido in atividade['nao_resolvidos']:
        if nao_resolvido['motivo'] != 'aluno_sem_lattes':
            nao_resolvidos.append(nao_resolvido['nome'])
    return {
        'id_atividade': atividade['codigo'], 'dimensao': atividade['dim'],
        'posicao_no_vetor': DIMENSOES.index(atividade['dim']) + 1,
        'tipo_atividade': NOME_DA_DIMENSAO[atividade['dim']], 'subtipo': atividade['subtipo'],
        'titulo': atividade['titulo'], 'ano': atividade['ano'], 'doi': atividade['doi'],
        'numero_registro': atividade['registro'],
        'aluno_ou_candidato': atividade['aluno_ou_candidato'],
        'periodo_projeto': atividade['periodo'], 'situacao_projeto': atividade['situacao'],
        'nomes_nao_resolvidos': ';'.join(nao_resolvidos),
        'registrado_no_cv_de': ';'.join(atividade['cvs']),
        'qtd_registros_unificados': atividade['quantidade_registros'],
        'fontes': ' || '.join(formatar_fonte(fonte) for fonte in atividade['fontes']),
        'chave_deduplicacao': atividade['chave'],
    }


def juntar_conjuntos(atividade, ids, campo):
    """ex: 'autor/membro;orientador'"""
    textos = []
    for pessoa in ids:
        textos.append('/'.join(sorted(atividade['participantes'][pessoa][campo])))
    return ';'.join(textos)


def formatar_fonte(fonte):
    """'<id>|<subtipo>|item <n>' -> '<id>:<subtipo>#<n>'"""
    dono, subtipo, numero = fonte.split('|')
    return f"{dono}:{subtipo}#{numero.replace('item ', '')}"
