# constantes usadas na mineração
from pathlib import Path

# caminhos
RAIZ = Path(__file__).parent
ENTRADA_PADRAO = RAIZ / 'dados' / 'brutos' / 'Professores_v8.zip'
SAIDA_PADRAO = RAIZ.parent / 'data' / 'raw'  # CSVs vão direto para backend/data/raw
PASTA_TEMPORARIOS = RAIZ / 'dados' / 'temporarios'
ARQUIVO_CORRESPONDENCIAS = RAIZ / 'correspondencias_confirmadas.json'

# camada e dimensões
CAMADA = 'IMC'

# ordem das posições do vetor
DIMENSOES = ['ART', 'PRJ', 'ORI', 'BAN', 'PTT']

NOME_DA_DIMENSAO = {
    'ART': 'Artigo científico',
    'PRJ': 'Projeto de pesquisa',
    'ORI': 'Orientação concluída',
    'BAN': 'Banca acadêmica',
    'PTT': 'Produção técnico-tecnológica',
}

# coluna de cada dimensão no dataset de entrada
COLUNA_DA_DIMENSAO = {
    'ART': 'artigos científicos',
    'PRJ': 'projetos de pesquisa',
    'ORI': 'orientação',
    'BAN': 'bancas acadêmicas',
    'PTT': 'produção técnico-tecnológica',
}

# papéis que contam como colaboração
# orientação: só conta quem orientou junto, o aluno não
PAPEIS_DE_SUPERVISAO = {'orientador', 'coorientador', 'orientador (não especificado)'}
PAPEL_DE_ORIENTANDO = 'orientando'
# banca: quem tem 'candidato' no papel é quem foi avaliado
PAPEL_DE_MEMBRO_DE_BANCA = 'membro'
PALAVRA_DE_CANDIDATO = 'candidato'

# nomes que não são pessoas
# palavras que indicam instituição/endereço (já sem acento)
PALAVRAS_DE_INSTITUICAO = {'UNIVERSIDADE', 'UNIVERSITY', 'UNIVERSIDAD', 'INSTITUTO', 'INSTITUTE',
                           'FACULDADE', 'DEPARTAMENTO', 'LABORATORIO', 'LTDA', 'FINANCIADORA'}

# externos com nome do meio faltando
# mínimo de coautores em comum pra juntar (evita homônimos)
COAUTORES_EM_COMUM_PARA_JUNTAR = 1

# institutos
# primeira palavra da pasta -> sigla
SIGLA_POR_PASTA = {
    'IEDU': 'IEDU', 'IEM': 'IEM', 'IEPG': 'IEPG', 'IESTI': 'IESTI', 'IFQ': 'IFQ',
    'IMC': 'IMC', 'IRN': 'IRN', 'ISEE': 'ISEE',
    'UA1': 'ICT', 'UA2': 'IEI', 'UA3': 'ICPA', 'UNIFEI': 'UNIFEI - PA',
    'ICT': 'ICT', 'IEI': 'IEI', 'ICPA': 'ICPA',
}

# seções do Lattes
SECAO_PRODUCOES = 'Produções'
SECAO_PATENTES = 'Patentes e registros'
SECAO_ORIENTACOES = 'Orientações'
SECAO_BANCAS = 'Bancas'
SECAO_PROJETOS = 'Projetos de pesquisa'

# subseção de Produções -> subtipo
SUBSECOES_ARTIGOS = {
    'Artigos completos publicados em periódicos': 'Artigo completo em periódico',
    'Trabalhos completos publicados em anais de congressos':
        'Trabalho completo em anais de congresso',
}
SUBSECOES_PRODUCAO_TECNICA = [
    'Assessoria e consultoria',
    'Demais tipos de produção técnica',
    'Entrevistas, mesas redondas, programas e comentários na mídia',
    'Processos ou técnicas',
    'Produtos tecnológicos',
    'Programas de computador sem registro',
    'Redes sociais, websites e blogs',
    'Trabalhos técnicos',
    'Apresentações de Trabalho',
]
BLOCOS_PATENTES = ['Patente', 'Programa de computador', 'Marca registrada', 'Desenho industrial']
# só orientações concluídas
BLOCO_ORIENTACOES = 'Orientações e supervisões concluídas'
PREFIXO_BANCAS_TRABALHOS = 'Participação em bancas de trabalhos de conclusão'
PREFIXO_BANCAS_COMISSOES = 'Participação em bancas de comissões julgadoras'

# tamanho máximo do texto guardado de cada item
TAMANHO_MAXIMO_DO_TEXTO = 1500

# deduplicação
# 'Atual' vira esse ano
ANO_ATUAL_DOS_PROJETOS = 2026
# semelhança mínima de título (difflib) pra juntar orientações e bancas
SIMILARIDADE_ORIENTACAO_ENTRE_CVS = 0.6
SIMILARIDADE_ORIENTACAO_MESMO_CV = 0.9
SIMILARIDADE_BANCA_ENTRE_CVS = 0.5
SIMILARIDADE_BANCA_MESMO_CV = 0.9
# candidato escrito diferente em cada CV ('Jr' x 'Junior', 'Rezende' x 'Resende')
SIMILARIDADE_BANCA_CANDIDATO_DIFERENTE = 0.8
PALAVRAS_EM_COMUM_DO_CANDIDATO = 2
# títulos quase idênticos
TITULO_QUASE_IDENTICO = 0.92
# só compara títulos que começam igual (40 caracteres)
PREFIXO_DO_TITULO = 40
# título idêntico com menos de 3 palavras é genérico demais
MIN_PALAVRAS_TITULO_IDENTICO = 3
# título parecido precisa de pelo menos 4 palavras
MIN_PALAVRAS_TITULO_SEMELHANTE = 4
