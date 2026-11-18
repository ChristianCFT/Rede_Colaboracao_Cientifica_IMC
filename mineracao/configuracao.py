"""Todas as constantes do projeto num lugar só: caminhos, camada, siglas, seções e limiares.

Nenhum outro arquivo tem números ou nomes de seção soltos: para mudar uma regra fixa, mude aqui.
"""
from pathlib import Path

# ---------------------------------------------------------------- caminhos padrão
RAIZ = Path(__file__).parent
ENTRADA_PADRAO = RAIZ / 'dados' / 'brutos' / 'Professores_v7_somente_HTML.zip'
SAIDA_PADRAO = RAIZ / 'dados_gerados'
PASTA_TEMPORARIOS = RAIZ / 'dados' / 'temporarios'
ARQUIVO_CORRESPONDENCIAS = RAIZ / 'correspondencias_confirmadas.json'

# ---------------------------------------------------------------- camada e dimensões
# Instituto central da rede: o pesquisador 1 de toda relação é deste instituto.
CAMADA = 'IMC'

# As cinco dimensões, sempre nesta ordem (é a ordem das posições do vetor).
DIMENSOES = ['ART', 'PRJ', 'ORI', 'BAN', 'PTT']

NOME_DA_DIMENSAO = {
    'ART': 'Artigo científico',
    'PRJ': 'Projeto de pesquisa',
    'ORI': 'Orientação concluída',
    'BAN': 'Banca acadêmica',
    'PTT': 'Produção técnico-tecnológica',
}

# Nome da coluna de cada dimensão no dataset de entrada.
COLUNA_DA_DIMENSAO = {
    'ART': 'artigos científicos',
    'PRJ': 'projetos de pesquisa',
    'ORI': 'orientação',
    'BAN': 'bancas acadêmicas',
    'PTT': 'produção técnico-tecnológica',
}

# ---------------------------------------------------------------- institutos
# Primeira palavra do nome da pasta do instituto -> sigla oficial (SIGAA UNIFEI).
SIGLA_POR_PASTA = {
    'IEDU': 'IEDU', 'IEM': 'IEM', 'IEPG': 'IEPG', 'IESTI': 'IESTI', 'IFQ': 'IFQ',
    'IMC': 'IMC', 'IRN': 'IRN', 'ISEE': 'ISEE',
    'UA1': 'ICT', 'UA2': 'IEI', 'UA3': 'ICPA', 'UNIFEI': 'UNIFEI - PA',
    'ICT': 'ICT', 'IEI': 'IEI', 'ICPA': 'ICPA',
}

# ---------------------------------------------------------------- seções do Lattes
SECAO_PRODUCOES = 'Produções'
SECAO_PATENTES = 'Patentes e registros'
SECAO_ORIENTACOES = 'Orientações'
SECAO_BANCAS = 'Bancas'
SECAO_PROJETOS = 'Projetos de pesquisa'

# Subseção de 'Produções' -> subtipo gravado na atividade.
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
# Só as orientações concluídas entram (as "em andamento" ficam de fora).
BLOCO_ORIENTACOES = 'Orientações e supervisões concluídas'
PREFIXO_BANCAS_TRABALHOS = 'Participação em bancas de trabalhos de conclusão'
PREFIXO_BANCAS_COMISSOES = 'Participação em bancas de comissões julgadoras'

# O texto de cada item é guardado só até este tamanho (serve para achar repetições idênticas).
TAMANHO_MAXIMO_DO_TEXTO = 1500

# ---------------------------------------------------------------- deduplicação
# Um projeto com período '2019 - Atual' é tratado como indo até este ano.
ANO_ATUAL_DOS_PROJETOS = 2026
# Semelhança mínima de título (0 a 1, difflib) para juntar duas orientações ou bancas.
SIMILARIDADE_ORIENTACAO_ENTRE_CVS = 0.6
SIMILARIDADE_ORIENTACAO_MESMO_CV = 0.9
SIMILARIDADE_BANCA_ENTRE_CVS = 0.5
SIMILARIDADE_BANCA_MESMO_CV = 0.9
# Títulos com semelhança >= 0,92 são "quase idênticos" (artigos, produção técnica, projetos).
TITULO_QUASE_IDENTICO = 0.92
# Só se comparam registros cujos títulos começam pelos mesmos 40 caracteres normalizados.
PREFIXO_DO_TITULO = 40
# Título idêntico com menos de 3 palavras é genérico demais para juntar sozinho.
MIN_PALAVRAS_TITULO_IDENTICO = 3
# Título só parecido precisa de pelo menos 4 palavras.
MIN_PALAVRAS_TITULO_SEMELHANTE = 4
