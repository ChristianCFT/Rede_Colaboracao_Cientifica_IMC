#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
analise_camadas.py - ANÁLISE DO IMC EM QUATRO CAMADAS

  Camada 1 - Núcleo Computação : docentes do IMC com área de Computação; laços entre eles.
  Camada 2 - Intra-IMC         : todos os docentes do IMC; laços entre eles.
  Camada 3 - Interdepartamental: camada 2 + laços dos docentes do IMC com pesquisadores
                                 de outros institutos da UNIFEI (sem externos).
  Camada 4 - Rede Completa     : toda a base; ligações com externos (EXT) por tipo do docente da UNIFEI.

Peso dos laços: seção 3.1.4 do relatório (W = Σ alfa_k * ln(1+x_k)/ln(1+xmax_k), em [0,1]).
Algoritmos (grafos_smac03.py): componentes (BFS), pontos de articulação (Tarjan).

USO
    Rode sem argumentos (botão play). Roda duas vezes: base completa e recorte 2016-2026.
"""
import collections
import json
import math
import os
from types import SimpleNamespace

import pandas as pd

import grafos_smac03 as gs

PASTA = os.path.dirname(os.path.abspath(__file__))
# cadastro completo (área de atuação); aceita o nome com ou sem o prefixo do upload
COMPLETO = next(c for c in ['dataset_completo_UNIFEI.csv', '755a6011-dataset_completo_UNIFEI.csv']
                if os.path.exists(os.path.join(PASTA, c)))
BASES = [
    ('dataset_IMC_2016_2026.xlsx', 'recorte 2016-2026'),
]

DIM = ['ART', 'PRJ', 'ORI', 'BAN', 'PTT']
PESOS = {'ART': 4.0, 'PRJ': 2.0, 'ORI': 2.0, 'PTT': 1.5, 'BAN': 0.5}
ALFA = {d: PESOS[d] / sum(PESOS.values()) for d in DIM}
INST = 'IMC'
EXT = 'EXT'
L = '─'
W_NOME = 30


def classe(area_txt):
    """CC = Ciência da Computação em qualquer área; MAT = 1ª área Matemática; OUTRA = demais."""
    if 'Ciência da Computação' in area_txt:
        return 'CC'
    primeira = area_txt.split(';')[0].strip()
    if 'Matemática' in primeira:          # formato do cadastro: "Grande área / Área"
        return 'MAT'
    return 'OUTRA'


def tipo(x, inst, cls):
    """Rótulo do tipo de nó para a distribuição de peso por tipo de laço."""
    if inst[x] == INST:
        return cls.get(x, 'OUTRA')
    if inst[x] == EXT:
        return 'EXT'
    return 'UNIFEI'


def rodar(base, rotulo):
    a = SimpleNamespace(base=os.path.join(PASTA, base), completo=os.path.join(PASTA, COMPLETO), rotulo=rotulo)

    d = pd.read_excel(a.base, sheet_name=['entrada', 'saida'], dtype=str)
    ent, sa = d['entrada'], d['saida'].fillna('')
    comp = pd.read_csv(a.completo, dtype=str, encoding='utf-8-sig').fillna('')
    inst = dict(zip(ent.pesquisador_id, ent.instituto))
    nome = dict(zip(ent.pesquisador_id, ent['nome do pesquisador']))
    area = dict(zip(comp.pesquisador_id, comp.area))
    cls = {i: classe(area.get(i, '')) for i in inst if inst[i] == INST}

    # pares únicos com vetor bruto
    P = {}
    for x, y, v in zip(sa['id pesquisador 1'], sa['id pesquisador 2'], sa['vetor contagem']):
        k = tuple(sorted([x, y]))
        if k not in P:
            P[k] = [int(t) for t in json.loads(v)]
    xmax = {dm: max(c[i] for c in P.values()) for i, dm in enumerate(DIM)}
    W = {k: sum(ALFA[dm] * math.log1p(c[i]) / math.log1p(xmax[dm]) for i, dm in enumerate(DIM))
         for k, c in P.items()}
    for k in P:
        P[k] = W[k]

    # conjuntos de nós por camada
    imc = [i for i in inst if inst[i] == INST]
    L1 = {i for i in imc if cls[i] == 'CC'}
    L2 = set(imc)
    L3 = set(imc) | {y for k in P for y in k if inst[y] not in (INST, EXT)
                     and any(inst[z] == INST for z in k)}
    L4 = set(inst)

    def arestas_da_camada(nos, camada):
        if camada == 4:
            return list(P)
        if camada == 3:
            return [k for k in P if any(x in L2 for x in k) and all(inst[x] != EXT for x in k)]
        return [k for k in P if k[0] in nos and k[1] in nos]

    camadas = [
        (1, 'Núcleo Computação', L1, 'docentes do IMC com área de Computação; laços entre eles'),
        (2, 'Intra-IMC', L2, 'todos os docentes do IMC; laços entre eles'),
        (3, 'Interdepartamental', L3, 'camada 2 + laços do IMC com outros institutos da UNIFEI'),
        (4, 'Rede Completa', L4, 'toda a base; ligações MAT/CC/UNIFEI/OUTRA com externos (EXT)'),
    ]

    # cabeçalho
    print('╔' + '═' * 78 + '╗')
    print('║' + f'  ANÁLISE DO IMC POR CAMADAS  ·  {a.rotulo}'.ljust(78) + '║')
    print('╚' + '═' * 78 + '╝')
    print(f'  Peso dos laços: seção 3.1.4 (α = 0,40 ART · 0,20 PRJ · 0,20 ORI · 0,15 PTT · 0,05 BAN)')
    print(f'  Laços na base: {len(P)} | docentes do IMC: {len(imc)} | '
          f'docentes com Computação: {len(L1)} | Matemática (1ª área): '
          f'{sum(1 for i in imc if cls[i] == "MAT")}')
    print()

    def relacao_com_externos(arestas_):
        """Laços entre um docente da UNIFEI e um externo, agrupados pelo tipo do docente.
        EXT–EXT é devolvido à parte, como referência."""
        rel = {r: {'laços': 0, 'peso': 0.0, 'ext': set(), 'doc': set()} for r in ['MAT', 'CC', 'UNIFEI', 'OUTRA']}
        ext_ext = {'laços': 0, 'peso': 0.0}
        for (u, v) in arestas_:
            eu, ev = inst[u] == EXT, inst[v] == EXT
            if eu and ev:
                ext_ext['laços'] += 1
                ext_ext['peso'] += P[(u, v)]
                continue
            if not (eu or ev):
                continue
            e, x = (u, v) if eu else (v, u)
            r = rel[tipo(x, inst, cls)]
            r['laços'] += 1
            r['peso'] += P[(u, v)]
            r['ext'].add(e)
            r['doc'].add(x)
        return rel, ext_ext

    rel4, ext_ext4 = relacao_com_externos(list(P))
    linhas = []
    detalhes = []
    for num, titulo, nos, escopo in camadas:
        arestas = arestas_da_camada(nos, num)
        G = gs.de_arestas([(u, v, P[(u, v)]) for (u, v) in arestas])
        for x in nos:
            G.setdefault(x, {})
        n = len(G)
        m = len(arestas)
        dens = gs.densidade(G)
        comps = gs.componentes(G)
        art, pontes = gs.articulacao_e_pontes(G)
        peso = sum(P[k] for k in arestas)
        # coesão: peso dentro da camada / peso de todos os laços que tocam a camada
        tocam = [k for k in P if k[0] in nos or k[1] in nos]
        peso_toca = sum(P[k] for k in tocam)
        coesao = 100 * peso / peso_toca if peso_toca else 0.0
        linhas.append((num, titulo, n, m, dens, len(comps), len(comps[0]) if comps else 0,
                       peso, peso / m if m else 0.0, len(art), coesao))

        # distribuição do peso por tipo de laço
        tip = collections.Counter()
        for (u, v) in arestas:
            rotulo = '–'.join(sorted([tipo(u, inst, cls), tipo(v, inst, cls)]))
            tip[rotulo] += P[(u, v)]
        # força dentro da camada
        forca = collections.Counter()
        for (u, v) in arestas:
            forca[u] += P[(u, v)]
            forca[v] += P[(u, v)]
        if num == 4:   # destaques da camada 4 sem externos
            forca = collections.Counter()
            for (u, v) in arestas:
                if inst[u] != EXT and inst[v] != EXT:
                    forca[u] += P[(u, v)]
                    forca[v] += P[(u, v)]
        top = forca.most_common(3)
        detalhes.append((num, titulo, escopo, tip, peso, top, n, m, dens, len(comps),
                         len(comps[0]) if comps else 0, len(art), len(pontes), coesao))

    # tabela resumo (larguras fixas)
    cols = [('Camada', 24, '<'), ('Nós', 6, '>'), ('Laços', 7, '>'), ('Densidade', 10, '>'),
            ('Compon.', 8, '>'), ('Maior', 6, '>'), ('Peso total', 11, '>'), ('Peso médio', 11, '>'),
            ('Coesão', 8, '>')]
    def celula(txt, w, al):
        return f' {txt:{al}{w}} '
    borda = lambda e, m, d: e + m.join('─' * (w + 2) for _, w, _ in cols) + d
    print(borda('┌', '┬', '┐'))
    print('│' + '│'.join(celula(c, w, al) for c, w, al in cols) + '│')
    print(borda('├', '┼', '┤'))
    for (num, titulo, n, m, dens, nc, maior, peso, pm, art, coesao) in linhas:
        vals = [f'{num}. {titulo}', f'{n}', f'{m}', f'{dens:.3f}', f'{nc}', f'{maior}',
                f'{peso:.2f}', f'{pm:.3f}', f'{coesao:.1f}%']
        print('│' + '│'.join(celula(v, w, al) for v, (_, w, al) in zip(vals, cols)) + '│')
    print(borda('└', '┴', '┘'))
    print('  Coesão = peso dentro da camada ÷ peso de todos os laços que tocam a camada.')
    print('  Maior = nós da maior componente conexa.')
    print()

    # detalhe por camada
    for (num, titulo, escopo, tip, peso, top, n, m, dens, nc, maior, art, pontes, coesao) in detalhes:
        print(f'┏━ CAMADA {num} · {titulo.upper()} ' + '━' * max(0, 60 - len(titulo)))
        print(f'┃  Escopo: {escopo}')
        print(f'┃  Nós {n} · laços {m} · densidade {dens:.3f} · componentes {nc} '
              f'(maior: {maior}) · articulações {art} · pontes {pontes}')
        print(f'┃  Peso total {peso:.2f} · coesão {coesao:.1f}%')
        print('┃')
        if num == 4:
            tot_p = sum(r['peso'] for r in rel4.values()) or 1.0
            print('┃  Ligações com externos (EXT), por tipo do docente da UNIFEI:')
            for rot in ['MAT', 'CC', 'UNIFEI', 'OUTRA']:
                r = rel4[rot]
                pl = r['peso'] / r['laços'] if r['laços'] else 0.0
                barra = '█' * int(round(30 * r['peso'] / tot_p))
                print(f'┃    {rot + "–EXT":<14} {r["peso"]:>9.2f}  {barra:<30}  '
                      f'laços {r["laços"]:>5} · peso/laço {pl:.3f} · externos {len(r["ext"])} · docentes {len(r["doc"])}')
            tot_l = sum(r['laços'] for r in rel4.values())
            print(f'┃    {"total EXT":<14} {tot_p:>9.2f}  laços {tot_l}')
            print(f'┃    fora do recorte acima: EXT–EXT com {ext_ext4["laços"]} laços e peso {ext_ext4["peso"]:.2f}')
        else:
            print('┃  Peso por tipo de laço:')
            total = sum(tip.values()) or 1.0
            for rot, val in tip.most_common():
                barra = '█' * int(round(30 * val / total))
                print(f'┃    {rot:<14} {val:>9.2f}  {100 * val / total:>5.1f}%  {barra}')
        print('┃')
        print('┃  Maior força dentro da camada' + (' (sem externos):' if num == 4 else ':'))
        for i, (x, f) in enumerate(top, 1):
            print(f'┃    {i}. {nome[x]:<{W_NOME}} {f:>7.2f}')
        print('┗' + '━' * 68)
        print()

    # conferências
    print('CONFERÊNCIAS')
    l2_ok = len(arestas_da_camada(L2, 2))
    l4_ok = len(arestas_da_camada(L4, 4))
    print(f'  Camada 4 contém todos os laços: {"OK" if l4_ok == len(P) else "ERRO"} ({l4_ok} de {len(P)})')
    print(f'  Camada 2 = laços IMC-IMC: {"OK" if l2_ok == sum(1 for k in P if inst[k[0]] == INST and inst[k[1]] == INST) else "ERRO"}')
    print(f'  Camada 1 ⊂ Camada 2: {"OK" if L1 <= L2 else "ERRO"}')
    n_ext = sum(1 for k in P if inst[k[0]] == EXT or inst[k[1]] == EXT)
    soma_rel = sum(r['laços'] for r in rel4.values()) + ext_ext4['laços']
    print(f'  Camada 4: laços com EXT (por tipo + EXT–EXT) = total de pares com EXT: {"OK" if soma_rel == n_ext else "ERRO"} ({soma_rel} de {n_ext})')


if __name__ == '__main__':
    for _base, _rot in BASES:
        rodar(_base, _rot)
