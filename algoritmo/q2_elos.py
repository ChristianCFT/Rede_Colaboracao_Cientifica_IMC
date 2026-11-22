#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
q2_elos.py - ELOS DE LIGAÇÃO DO IMC E SIMULAÇÃO DE REMOÇÃO

Pergunta: quais docentes do IMC conectam o instituto a outros institutos e a pesquisadores
externos (EXT), e o que acontece com a rede se eles saírem do cenário?

ESCOPO: somente docentes da UNIFEI (IMC e demais institutos). Pesquisadores externos (EXT) são
excluídos da rede, junto com todos os laços que tocam um externo. Os pesos W continuam normalizados
pela base completa do recorte, para que sejam comparáveis aos do Q1.

Duas análises, com o mesmo procedimento:
  A) elos escolhidos pelo PESO das ligações fora do IMC;
  B) elos escolhidos pela QUANTIDADE de ligações fora do IMC (nº de laços, sem peso).

USO
    Rode sem argumentos (botão play). Roda duas vezes: base completa e recorte 2016-2026.
"""
import json
import math
import os

import networkx as nx
import pandas as pd

PASTA = os.path.dirname(os.path.abspath(__file__))
BASES = [
    ('dataset_IMC_2016_2026.xlsx', 'RECORTE 2016-2026'),
]
TOP = 3

# =============================================================================
# 0. CONSTANTES
#    (MATÉRIA: Grafos ponderados - a equação de pesos do grupo)
# =============================================================================
DIM = ['ART', 'PRJ', 'ORI', 'BAN', 'PTT']                 # ordem do vetor contagem
PESOS = {'ART': 4.0, 'PRJ': 2.0, 'ORI': 2.0, 'PTT': 1.5, 'BAN': 0.5}
ALFA = {d: PESOS[d] / sum(PESOS.values()) for d in DIM}   # alfa = (0,40; 0,20; 0,20; 0,15; 0,05)
INST = 'IMC'
EXT = 'EXT'


# =============================================================================
# 1. LEITURA E REDE
#    (MATÉRIA: Representação de grafos - lista de arestas; grafo não direcionado)
# =============================================================================
def carregar(arquivo):
    d = pd.read_excel(arquivo, sheet_name=['entrada', 'saida'], dtype=str)
    ent = d['entrada']
    assert ent['pesquisador_id'].is_unique, 'pesquisador_id duplicado na entrada'
    return ent, d['saida'].fillna('')


def construir_rede(ent, sa):
    """Vértices: todos os ids que aparecem na saída; instituto vem do cadastro (entrada).
    Arestas: pares únicos (cada par IMC-IMC aparece nos dois sentidos com o mesmo vetor).
    Peso: 4*ART + 2*PRJ + 2*ORI + 1,5*PTT + 0,5*BAN."""
    inst = dict(zip(ent['pesquisador_id'], ent['instituto']))
    G = nx.Graph()
    vistos = {}
    for a, b, v in zip(sa['id pesquisador 1'], sa['id pesquisador 2'], sa['vetor contagem']):
        assert a != b, 'laço consigo mesmo'
        k = tuple(sorted([a, b]))
        c = [int(x) for x in json.loads(v)]
        if k in vistos:
            assert vistos[k] == c, f'par {k} com vetores diferentes nos dois sentidos'
            continue
        vistos[k] = c
    # xmax sobre a base completa (mesma escala do Q1): W = Σ alfa_k * ln(1+x_k) / ln(1+xmax_k)
    xmax = {d: max(c[i] for c in vistos.values()) for i, d in enumerate(DIM)}
    # escopo: só UNIFEI; laços que tocam um externo (EXT) ficam de fora
    unifei = {k: c for k, c in vistos.items() if inst[k[0]] != EXT and inst[k[1]] != EXT}
    # todos os docentes da UNIFEI entram como vértice, mesmo sem laço dentro da UNIFEI
    G.add_nodes_from({n for k in vistos for n in k if inst[n] != EXT})
    for (a, b), c in unifei.items():
        w = sum(ALFA[d] * math.log1p(n) / math.log1p(xmax[d]) for d, n in zip(DIM, c))
        G.add_edge(a, b, weight=w)
    for n in G:
        assert n in inst, f'id {n} sem cadastro na entrada'
        G.nodes[n]['inst'] = inst[n]
    return G, len(unifei), sum(1 for (a, b) in unifei if inst[a] == INST and inst[b] == INST)


# =============================================================================
# 2. ELOS
#    (MATÉRIA: Centralidade de intermediação - betweenness; grau ponderado - força)
# =============================================================================
def candidatos(G):
    """Docentes do IMC com ao menos uma ligação fora do IMC, com suas medidas externas."""
    dados = []
    for n in G:
        if G.nodes[n]['inst'] != INST:
            continue
        ext = [m for m in G[n] if G.nodes[m]['inst'] != INST]
        if not ext:
            continue
        peso_ext = sum(G[n][m]['weight'] for m in ext)
        peso_tot = sum(d['weight'] for *_, d in G.edges(n, data=True))
        dados.append({'id': n, 'lacos_ext': len(ext), 'peso_ext': peso_ext,
                      'pct_ext': 100 * peso_ext / peso_tot,
                      'grupos': sorted({G.nodes[m]['inst'] for m in ext})})
    return pd.DataFrame(dados)


def intermediacao(G):
    """Intermediação ponderada (amostrada): distância do laço = 1/peso (laço forte = caminho curto).
    (MATÉRIA: caminhos mínimos, Dijkstra; centralidade de intermediação)"""
    H = G.copy()
    for u, v, d in H.edges(data=True):
        d['dist'] = 1.0 / d['weight']
    # rede grande (11.630 nós): amostragem com 800 origens e semente fixa (reprodutível)
    return nx.betweenness_centrality(H, k=min(800, len(H)), weight='dist', normalized=True, seed=42)


# =============================================================================
# 3. SIMULAÇÃO DE REMOÇÃO
#    (MATÉRIA: Componentes conexos (BFS/DFS); robustez de redes a remoção de vértices)
# =============================================================================
def cenario(G, R, c0):
    """Remove o conjunto R de docentes (com todos os seus laços) e mede o efeito.
    c0 = conjunto de nós do componente principal ORIGINAL."""
    R = set(R)
    H = G.copy()
    H.remove_nodes_from(R)
    comps = sorted(nx.connected_components(H), key=len, reverse=True)
    principal = comps[0] if comps else set()
    restantes_c0 = c0 - R
    desconectados = restantes_c0 - principal
    com_laco = [v for v in G if v not in R and G.degree(v) > 0]
    pontas = [v for v in com_laco if H.degree(v) == 0]
    arestas_perdidas = {frozenset((u, v)) for u in R for v in G[u]}
    peso_perdido = sum(G[tuple(e)[0]][tuple(e)[1]]['weight'] for e in arestas_perdidas)
    peso_total = sum(d['weight'] for *_, d in G.edges(data=True))
    imc_restantes = [v for v in G if v not in R and G.nodes[v]['inst'] == INST]
    imc_desc = [v for v in desconectados if G.nodes[v]['inst'] == INST]
    return {
        'componentes_apos': len(comps),
        'principal_apos': len(principal),
        'n_desconectados': len(desconectados),
        'pct_desconectados': 100 * len(desconectados) / len(restantes_c0) if restantes_c0 else 0.0,
        'pontas': len(pontas),
        'pontas_imc': sum(1 for v in pontas if G.nodes[v]['inst'] == INST),
        'pct_pontas': 100 * len(pontas) / len(com_laco) if com_laco else 0.0,
        'imc_desconectados': len(imc_desc),
        'pct_imc_desconectados': 100 * len(imc_desc) / len(imc_restantes) if imc_restantes else 0.0,
        'arestas_perdidas': len(arestas_perdidas),
        'pct_peso_perdido': 100 * peso_perdido / peso_total,
    }


# =============================================================================
# 4. APRESENTAÇÃO
# =============================================================================
def curto(nome):
    nome = str(nome).title() if str(nome).isupper() else str(nome)
    p = [x for x in nome.split() if x.lower() not in ('de', 'da', 'do', 'das', 'dos', 'e')]
    return p[0] + (' ' + p[-1] if len(p) > 1 else '')


def rodar_analise(titulo, G, cand, criterio, top, nome, c0, linha):
    ordem = cand.sort_values([criterio, 'id'], ascending=[False, True]).head(top)
    elos = list(ordem.id)
    print('\n' + linha + f'\n{titulo}\n' + linha)
    print(f'  critério de escolha: {criterio} (maior primeiro; empate por id)')
    print(f'  {"#":<3}{"elo":<28}{"laços fora":>11}{"peso fora":>11}{"% peso fora":>13}  grupos alcançados')
    for i, r in enumerate(ordem.itertuples(), 1):
        print(f'  {i:<3}{curto(nome[r.id]):<28}{r.lacos_ext:>11}{r.peso_ext:>11.3f}{r.pct_ext:>12.1f}%  {", ".join(r.grupos)}')

    print('\n  Remoção INDIVIDUAL de cada elo:')
    print(f'  {"elo retirado":<28}{"comp.":>6}{"desconect.":>12}{"pontas (IMC)":>15}{"IMC desconect.":>16}{"peso perdido":>14}')
    for e in elos:
        s = cenario(G, {e}, c0)
        print(f'  {curto(nome[e]):<28}{s["componentes_apos"]:>6}{s["pct_desconectados"]:>11.2f}%'
              f'{s["pontas"]:>9} ({s["pontas_imc"]:>2}){s["pct_imc_desconectados"]:>14.1f}%{s["pct_peso_perdido"]:>13.2f}%')

    s = cenario(G, set(elos), c0)
    print('\n  Remoção CONJUNTA dos elos (todos de uma vez):')
    print(f'    componentes após a remoção ....... {s["componentes_apos"]}')
    print(f'    componente principal ............. {s["principal_apos"]} nós')
    print(f'    desconectados do principal ....... {s["n_desconectados"]} nós ({s["pct_desconectados"]:.2f}% dos nós que restam do principal original)')
    print(f'    pontas soltas (sem nenhum laço) .. {s["pontas"]} nós ({s["pct_pontas"]:.2f}% dos nós restantes com laço), sendo {s["pontas_imc"]} do IMC')
    print(f'    docentes do IMC desconectados .... {s["imc_desconectados"]} ({s["pct_imc_desconectados"]:.1f}% dos docentes do IMC que restam)')
    print(f'    laços removidos .................. {s["arestas_perdidas"]} ({s["pct_peso_perdido"]:.2f}% do peso total da rede)')
    return elos, s


def rodar(arquivo, titulo):
    linha = '=' * 84
    ent, sa = carregar(arquivo)
    G, n_pares, n_imc_imc = construir_rede(ent, sa)
    nome = dict(zip(ent['pesquisador_id'], ent['nome do pesquisador']))
    comps = sorted(nx.connected_components(G), key=len, reverse=True)
    c0 = set(comps[0])
    imc = [n for n in G if G.nodes[n]['inst'] == INST]

    print(linha + f'\nQ2. ELOS DE LIGAÇÃO DO IMC - {titulo}\n' + linha)
    print('Pesos (seção 3.1.4): W = 0,40*z_ART + 0,20*z_PRJ + 0,20*z_ORI + 0,15*z_PTT + 0,05*z_BAN, z = ln(1+x)/ln(1+xmax)')
    print(f'Conferência: {len(sa)} linhas da saida = {n_pares} pares únicos ({n_imc_imc} IMC-IMC); '
          f'pares IMC-IMC com vetor idêntico nos dois sentidos  [OK]')
    print(f'\nREDE: {G.number_of_nodes()} nós | {G.number_of_edges()} laços | {len(comps)} componentes conexos | '
          f'componente principal: {len(c0)} nós ({100 * len(c0) / G.number_of_nodes():.1f}%)')
    print(f'DOCENTES DO IMC NA REDE: {len(imc)}')
    print('ESCOPO: somente UNIFEI (externos EXT excluídos da rede).')

    cand = candidatos(G)
    bet = intermediacao(G)
    cand['interm'] = cand.id.map(bet)
    print(f'\nCANDIDATOS: {len(cand)} docentes do IMC têm ligações fora do instituto '
          f'(de {len(imc)} docentes na rede).')

    rodar_analise('ANÁLISE A - elos pelo PESO das ligações fora do IMC', G, cand, 'peso_ext', TOP, nome, c0, linha)
    rodar_analise('ANÁLISE B - elos pela QUANTIDADE de ligações fora do IMC', G, cand, 'lacos_ext', TOP, nome, c0, linha)

    print(f'\nCANDIDATOS MAIS RELEVANTES (top 10 de {len(cand)} por peso fora do IMC)')
    print(f'  {"docente":<28}{"laços fora":>11}{"peso fora":>11}{"interm.":>10}')
    for r in cand.sort_values(['peso_ext', 'id'], ascending=[False, True]).head(10).itertuples():
        print(f'  {curto(nome[r.id]):<28}{r.lacos_ext:>11}{r.peso_ext:>11.3f}{r.interm:>10.4f}')
    print()


def main():
    for arquivo, titulo in BASES:
        rodar(os.path.join(PASTA, arquivo), titulo)


if __name__ == '__main__':
    main()
