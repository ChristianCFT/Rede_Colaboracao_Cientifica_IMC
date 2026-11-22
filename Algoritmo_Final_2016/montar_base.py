# -*- coding: utf-8 -*-
# Rode sem argumentos (botão play): gera dataset_IMC_2016_2026.xlsx a partir dos CSVs da mineração.
"""Monta a base das análises (Q1, Q2 e camadas) direto dos CSVs da mineração.

Substitui o build_base_v4.py no menu. Não reconstrói nada: a mineração já entrega
a rede do IMC pronta (recorte 2016-2026, regra de papéis e só relações com docente
do IMC). Este script só copia as colunas usadas pelas análises para as abas
"entrada" e "saida" do xlsx e confere se os dados estão coerentes.

Entrada: dataset_entrada_IMC.csv e dataset_saida_IMC.csv (e, só para conferir os
anos, dataset_atividades_IMC.csv).
Saída:   dataset_IMC_2016_2026.xlsx (abas LEIAME, entrada e saida).
"""
import json
import os

import pandas as pd

PASTA = os.path.dirname(os.path.abspath(__file__))
ARQ_ENTRADA = 'dataset_entrada_IMC.csv'
ARQ_SAIDA = 'dataset_saida_IMC.csv'
ARQ_ATIVIDADES = 'dataset_atividades_IMC.csv'
ARQ_XLSX = 'dataset_IMC_2016_2026.xlsx'
ANO_INICIAL, ANO_FINAL = 2016, 2026

# Só as colunas que q1_terminal.py, q2_elos.py e analise_camadas.py leem.
# As colunas com listas de atividades ficam de fora: são grandes demais para uma célula do Excel.
COLUNAS_ENTRADA = ['pesquisador_id', 'nome do pesquisador', 'instituto', 'area de trabalho']
COLUNAS_SAIDA = [
    'nome do pesquisador 1', 'nome do pesquisador 2',
    'instituto pesquisador 1', 'instituto pesquisador 2',
    'area de trabalho pesquisador 1', 'area de trabalho pesquisador 2',
    'id pesquisador 1', 'id pesquisador 2', 'vetor contagem',
]


def ler_csv(nome):
    caminho = os.path.join(PASTA, nome)
    if not os.path.exists(caminho):
        raise SystemExit(f'Arquivo não encontrado: {nome}')
    return pd.read_csv(caminho, dtype=str, encoding='utf-8-sig')


def conferir_colunas(tabela, colunas, nome):
    faltando = [c for c in colunas if c not in tabela.columns]
    if faltando:
        raise SystemExit(f'{nome}: faltam as colunas {faltando}')


def conferir_anos():
    """Avisa se a base de atividades tem ano fora do recorte (só aviso, não para)."""
    caminho = os.path.join(PASTA, ARQ_ATIVIDADES)
    if not os.path.exists(caminho):
        print(f'aviso: {ARQ_ATIVIDADES} não encontrado; anos não conferidos.')
        return
    anos = pd.read_csv(caminho, dtype=str, encoding='utf-8-sig', usecols=['ano'])['ano'].astype(int)
    fora = ((anos < ANO_INICIAL) | (anos > ANO_FINAL)).sum()
    print(f'anos das atividades: {anos.min()} a {anos.max()}', end='')
    if fora:
        print(f'  [AVISO: {fora} atividades fora de {ANO_INICIAL}-{ANO_FINAL}]')
    else:
        print('  [OK]')


def conferir_saida(entrada, saida):
    """Confere ids, vetores e os pares IMC-IMC (o Q1 exige os dois sentidos iguais)."""
    ids = set(entrada['pesquisador_id'])
    if not entrada['pesquisador_id'].is_unique:
        raise SystemExit('entrada: pesquisador_id repetido')
    for col in ['id pesquisador 1', 'id pesquisador 2']:
        sem_cadastro = set(saida[col]) - ids
        if sem_cadastro:
            raise SystemExit(f'saida: {len(sem_cadastro)} ids de "{col}" não estão na entrada')

    vetores = {}
    for a, b, v in zip(saida['id pesquisador 1'], saida['id pesquisador 2'], saida['vetor contagem']):
        vetor = json.loads(v)
        if len(vetor) != 5:
            raise SystemExit(f'saida: vetor com tamanho errado no par {a} - {b}')
        vetores[(a, b)] = vetor

    instituto = dict(zip(entrada['pesquisador_id'], entrada['instituto']))
    for (a, b), vetor in vetores.items():
        if instituto[a] == 'IMC' and instituto[b] == 'IMC' and vetores.get((b, a)) != vetor:
            raise SystemExit(f'saida: par IMC-IMC {a} - {b} sem o sentido inverso igual')
        if instituto[a] != 'IMC' and instituto[b] != 'IMC':
            raise SystemExit(f'saida: par {a} - {b} não tem docente do IMC')

    pares = {tuple(sorted(par)) for par in vetores}
    return pares, instituto


def resumo(pares, instituto):
    def tipo(i):
        if instituto[i] == 'IMC':
            return 'IMC'
        return 'externo' if instituto[i] == 'EXT' else 'UNIFEI'

    contagem = {}
    for a, b in pares:
        chave = ' - '.join(sorted((tipo(a), tipo(b))))
        contagem[chave] = contagem.get(chave, 0) + 1
    return contagem


def montar():
    entrada = ler_csv(ARQ_ENTRADA)
    saida = ler_csv(ARQ_SAIDA)
    conferir_colunas(entrada, COLUNAS_ENTRADA, ARQ_ENTRADA)
    conferir_colunas(saida, COLUNAS_SAIDA, ARQ_SAIDA)
    entrada = entrada[COLUNAS_ENTRADA]
    saida = saida[COLUNAS_SAIDA]

    conferir_anos()
    pares, instituto = conferir_saida(entrada, saida)
    com_relacao = {i for par in pares for i in par}
    tipos = resumo(pares, instituto)

    leia = pd.DataFrame({'LEIAME': [
        f'Base {ANO_INICIAL}-{ANO_FINAL} montada por montar_base.py a partir dos CSVs da mineração.',
        f'{ARQ_ENTRADA}: {len(entrada)} pessoas ({len(com_relacao)} com relação).',
        f'{ARQ_SAIDA}: {len(saida)} linhas = {len(pares)} relações únicas (IMC-IMC nos dois sentidos).',
        'Regras da mineração: só relações com docente do IMC; aluno orientado e candidato de banca não contam.',
        'Vetor contagem na ordem [ART, PRJ, ORI, BAN, PTT].',
    ]})
    with pd.ExcelWriter(os.path.join(PASTA, ARQ_XLSX), engine='openpyxl') as w:
        leia.to_excel(w, sheet_name='LEIAME', index=False)
        entrada.to_excel(w, sheet_name='entrada', index=False)
        saida.to_excel(w, sheet_name='saida', index=False)

    docentes_imc = sum(1 for t in entrada['instituto'] if t == 'IMC')
    print(f'pessoas: {len(entrada)} ({docentes_imc} docentes do IMC) | com relação: {len(com_relacao)}')
    print(f'relações únicas: {len(pares)} | linhas da saida: {len(saida)}')
    print('relações por tipo:', ', '.join(f'{k} {v}' for k, v in sorted(tipos.items())))
    print(f'gerado: {ARQ_XLSX}')


if __name__ == '__main__':
    montar()
