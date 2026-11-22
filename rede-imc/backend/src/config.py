import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / 'data' / 'raw'
FILES = dict(saida='dataset_saida_IMC.csv', entrada='dataset_entrada_IMC.csv',
             unifei='dataset_completo_UNIFEI.csv', atividades='dataset_atividades_IMC.csv')

# colunas usadas do dataset_atividades
COLUNAS_ATIVIDADES = ['id_atividade', 'ano', 'titulo']

DIMS = ['art', 'prj', 'ori', 'ban', 'ptt']  # ordem do vetor
DIMN = ['Artigos', 'Projetos', 'Orientações', 'Bancas', 'Prod. téc.']

# peso de cada dimensão (soma 1)
ALFAS = {'art': 0.40, 'prj': 0.20, 'ori': 0.20, 'ptt': 0.15, 'ban': 0.05}

# professor com várias áreas entra em todos os grupos
REGRAS_AREA = {'Computação': ['ciência da computação'],
               'Matemática': ['matemática', 'probabilidade e estatística']}

PALETA = {'IMC': '#d62728', 'EXT': '#9aa0a6', 'IFQ': '#1f77b4', 'IEM': '#ff7f0e', 'IEPG': '#2ca02c',
          'IESTI': '#9467bd', 'IRN': '#8c564b', 'ICPA': '#e377c2', 'IEDU': '#bcbd22', 'ICT': '#17becf',
          'ISEE': '#7f7f7f', 'IEI': '#393b79', 'UNIFEI - PA': '#ad494a'}
COR_GRUPO = {'Computação': '#2563eb', 'Matemática': '#f59e0b', 'Ambas': '#8b5cf6',
             'Outras': '#64748b', 'Sem área': '#94a3b8', 'cross': '#8b5cf6'}

CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:5173,http://127.0.0.1:5173').split(',')
API_PREFIX = '/api/v1'
