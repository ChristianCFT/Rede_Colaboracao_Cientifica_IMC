#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
q1_terminal.py - Questão 1: "Quais são os grupos do IMC?"

Rode sem argumentos (botão play). Roda duas vezes: base completa e recorte 2016-2026.

Monta a rede de colaboração entre os docentes do IMC (pares da aba saida, peso do modelo do
artigo, seção 3.1.4), acha os grupos com Louvain e imprime:
  - grupos principais, grupos menores, top 5 trios e top 3 docentes (ligações e peso).
"""
import itertools
import json
import os

import networkx as nx
import numpy as np
import pandas as pd
from sklearn.metrics import normalized_mutual_info_score as nmi

PASTA = os.path.dirname(os.path.abspath(__file__))
BASES = [
    ('dataset_IMC_2016_2026.xlsx', 'RECORTE 2016-2026'),
]
RESOLUCAO = 1.0          # grupos principais
TOP = 5                  # trios

DIM = ['ART', 'PRJ', 'ORI', 'BAN', 'PTT']
INST = 'IMC'
PESOS = {'ART': 4.0, 'PRJ': 2.0, 'ORI': 2.0, 'PTT': 1.5, 'BAN': 0.5}
ALFA = {d: PESOS[d] / sum(PESOS.values()) for d in DIM}
NM = {'CC': 'Computação', 'MAT': 'Matemática', 'OUTRA': 'Outra', 'AMBAS': 'Ambas', 'ND': 'Sem área'}


def carregar(arquivo):
    d = pd.read_excel(arquivo, sheet_name=['entrada', 'saida'], dtype=str)
    ent = d['entrada']
    assert ent['pesquisador_id'].is_unique, 'pesquisador_id duplicado na entrada'
    return ent, d['saida'].fillna('')


def pares_imc(sa):
    """Pares IMC-IMC sem duplicata; confere que os dois sentidos têm o mesmo vetor."""
    ii = sa[(sa['instituto pesquisador 1'] == INST) & (sa['instituto pesquisador 2'] == INST)]
    vistos = {}
    for a, b, v in zip(ii['id pesquisador 1'], ii['id pesquisador 2'], ii['vetor contagem']):
        assert a != b, 'laço consigo mesmo na saída'
        k = tuple(sorted([a, b]))
        c = [int(x) for x in json.loads(v)]
        if k in vistos:
            assert vistos[k] == c, f'par {k} com vetores diferentes nos dois sentidos'
        vistos[k] = c
    df = pd.DataFrame([(a, b, *c) for (a, b), c in vistos.items()], columns=['a', 'b'] + DIM)
    return df, len(ii)


def xmax_rede(sa):
    V = np.array([json.loads(v) for v in sa['vetor contagem']])
    return dict(zip(DIM, V.max(axis=0)))


def classe_area(txt):
    t = txt if isinstance(txt, str) else ''
    cc, mt = 'Ciência da Computação' in t, 'Matemática' in t
    if cc and mt:
        return 'AMBAS'
    return 'CC' if cc else 'MAT' if mt else ('OUTRA' if t else 'ND')


def peso_aresta(pares, xmax):
    """W = soma_k alfa_k * ln(1+x_k) / ln(1+xmax_k), em [0,1]."""
    p = pares.copy()
    p['W'] = sum(ALFA[d] * np.log1p(p[d]) / np.log1p(xmax[d]) for d in DIM)
    return p


def montar_grafo(pares, docs):
    G = nx.Graph()
    G.add_nodes_from(sorted(docs))
    for r in pares.itertuples(index=False):
        G.add_edge(r.a, r.b, weight=r.W)
    return G


def grupos_louvain(G, resolucao=1.0, seed=42, sementes=20):
    """Louvain com várias sementes; estabilidade = NMI médio entre as partições."""
    def rodar(s):
        p = nx.community.louvain_communities(G, weight='weight', resolution=resolucao, seed=s)
        p = sorted(p, key=lambda c: (-len(c), min(c)))
        return p, nx.community.modularity(G, p, weight='weight', resolution=resolucao)

    part, mod = rodar(seed)
    nos = list(G)
    rots = []
    for s in range(sementes):
        p, _ = rodar(s)
        lab = {n: k for k, c in enumerate(p) for n in c}
        rots.append([lab[n] for n in nos])
    estab = float(np.mean([nmi(x, y) for x, y in itertools.combinations(rots, 2)]))
    return part, mod, estab


def analisar(G, area, part):
    """Resumo por grupo: áreas e líderes (maior força)."""
    forca = dict(G.degree(weight='weight'))
    cls = {n: classe_area(area.get(n)) for n in G}
    linhas = []
    for k, c in enumerate(part, 1):
        lid = sorted(c, key=lambda n: (-forca[n], n))[:3]
        linhas.append({'grupo': k,
                       'areas': str(pd.Series([cls[n] for n in c]).value_counts().sort_index()
                                    .sort_values(ascending=False, kind='stable').to_dict()),
                       'lideres': ', '.join(NOME[n] for n in lid)})
    return pd.DataFrame(linhas), cls


def curto(nome):
    nome = str(nome).title() if str(nome).isupper() else str(nome)
    p = [x for x in nome.split() if x.lower() not in ('de', 'da', 'do', 'das', 'dos', 'e')]
    return p[0] + (' ' + p[-1] if len(p) > 1 else '')


def top_trios(G, n=TOP, chave='elo'):
    """Trios (triângulos) ranqueados pelo elo mais fraco (chave='elo') ou pela soma dos pesos (chave='soma')."""
    tri = []
    for c in nx.enumerate_all_cliques(G):
        if len(c) == 3:
            ws = [G[u][v]['weight'] for u, v in itertools.combinations(c, 2)]
            tri.append((min(ws), sum(ws), tuple(sorted(c))))
        elif len(c) > 3:
            break
    if chave == 'soma':
        tri.sort(key=lambda t: (-t[1], -t[0], t[2]))
    else:
        tri.sort(key=lambda t: (-t[0], -t[1], t[2]))
    return tri[:n], len(tri)


def top_docentes(G, chave, n=3):
    deg, st = dict(G.degree()), dict(G.degree(weight='weight'))
    a, b = (deg, st) if chave == 'grau' else (st, deg)
    ordem = sorted(G, key=lambda x: (-a[x], -b[x], x))
    top = ordem[:n]
    empatados = [x for x in ordem[n:] if a[x] == a[top[-1]]]
    return top, empatados, deg, st


NOME = {}


def rodar(arquivo, titulo):
    global NOME
    dec = 3
    ent, sa = carregar(arquivo)
    docs = set(ent.loc[ent['instituto'] == INST, 'pesquisador_id'])
    NOME = dict(zip(ent['pesquisador_id'], ent['nome do pesquisador']))
    area = dict(zip(ent['pesquisador_id'], ent['area de trabalho']))

    pares, linhas_lidas = pares_imc(sa)
    xm = xmax_rede(sa)
    pares = peso_aresta(pares, xm)
    G = montar_grafo(pares, docs)
    comp = list(nx.connected_components(G))
    isolados = [n for n in G if G.degree(n) == 0]

    part, mod, estab = grupos_louvain(G, RESOLUCAO)
    resumo, cls = analisar(G, area, part)
    nos = list(G)
    nmi_area = nmi([cls[n] for n in nos], [next(k for k, c in enumerate(part, 1) if n in c) for n in nos])
    grandes = [k for k, c in enumerate(part, 1) if len(c) >= 3]
    grupo_de = {x: k for k, c in enumerate(part, 1) for x in c}

    print('=' * 78)
    print(f'  {titulo}  ·  {arquivo}')
    print('=' * 78)
    print('Pesos (modelo do artigo): W = ' + ' + '.join(f'{ALFA[d]:.2f}*z_{d}' for d in ['ART', 'PRJ', 'ORI', 'PTT', 'BAN'])
          + ' | z = ln(1+x)/ln(1+xmax) | xmax: ' + ', '.join(f'{d} {int(xm[d])}' for d in DIM)
          + f' | min-w 0.0 | resolução {RESOLUCAO}')
    print(f'Conferência da aba saida: {linhas_lidas} linhas {INST}-{INST} = {len(pares)} pares únicos; '
          f'cada par com vetor idêntico nos dois sentidos  [OK]')
    print(f'\nGRAFO: {G.number_of_nodes()} docentes | {G.number_of_edges()} laços | densidade {nx.density(G):.3f} | '
          f'{len(comp)} componentes conexos (maior: {max(map(len, comp))}) | {len(isolados)} sem laço')
    print(f'\nLOUVAIN: {len(part)} grupos (tamanhos {[len(c) for c in part]}), {len(grandes)} com 3+ docentes')
    print(f'  modularidade Q = {mod:.3f} | estabilidade (NMI médio entre 20 sementes) = {estab:.2f} | NMI grupos x área = {nmi_area:.2f}')

    # ---- 2. TRIOS ----
    tri, ntri = top_trios(G, TOP)
    print('\n' + '-' * 78 + f'\n2. TOP {TOP} TRIOS MAIS FORTES (de {ntri} triângulos) - ranking pelo elo mais fraco\n' + '-' * 78)
    print('  elo fraco = menor peso entre os 3 pares | força = soma dos 3 pesos\n')
    for i, (mn, tot, c) in enumerate(tri, 1):
        print(f'  {i}. elo fraco {mn:>6.{dec}f} | força {tot:>7.{dec}f} | grupo {sorted({grupo_de[x] for x in c})} | '
              + ' + '.join(curto(NOME[x]) for x in sorted(c, key=lambda x: NOME[x])))

    # ---- 3. TRIOS POR SOMA ----
    tri_s, ntri_s = top_trios(G, TOP, chave='soma')
    print('\n' + '-' * 78 + f'\n3. TOP {TOP} TRIOS MAIS FORTES (de {ntri_s} triângulos) - ranking pela SOMA DOS PESOS\n' + '-' * 78)
    print('  soma = soma dos 3 pesos | elo fraco = menor peso entre os 3 pares\n')
    for i, (mn, tot, c) in enumerate(tri_s, 1):
        print(f'  {i}. soma {tot:>6.{dec}f} | elo fraco {mn:>6.{dec}f} | grupo {sorted({grupo_de[x] for x in c})} | '
              + ' + '.join(curto(NOME[x]) for x in sorted(c, key=lambda x: NOME[x])))

    # ---- 4 e 5. INFLUÊNCIA ----
    for titulo_inf, chave in [('4. TOP 3 DOCENTES COM MAIS INFLUÊNCIA POR LIGAÇÕES (nº de colegas)', 'grau'),
                              ('5. TOP 3 DOCENTES COM MAIS INFLUÊNCIA POR PESO (força = soma dos pesos)', 'peso')]:
        top, emp, deg, st = top_docentes(G, chave)
        print('\n' + '-' * 78 + '\n' + titulo_inf + '\n' + '-' * 78)
        for i, x in enumerate(top, 1):
            print(f'  {i}. {NOME[x]:<38} ligações {deg[x]:>2} | peso {st[x]:>7.{dec}f} | grupo {grupo_de[x]} | '
                  f'{NM[cls[x]]}')
        if emp:
            print(f'  (empate no {len(top)}º lugar em {"ligações" if chave == "grau" else "peso"}: '
                  + ', '.join(NOME[x] for x in emp) + '; desempate pelo outro critério)')
    print()


def main():
    for arquivo, titulo in BASES:
        rodar(os.path.join(PASTA, arquivo), titulo)


if __name__ == '__main__':
    main()
