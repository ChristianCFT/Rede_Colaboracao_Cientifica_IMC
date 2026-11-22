"""
Análise da rede de colaboração do IMC/UNIFEI.

Uso:
    python analise_rede_IMC.py              (procura os CSVs nesta pasta)
    python analise_rede_IMC.py <pasta_csv>

Se não achar os CSVs aqui, usa ../backend/data/raw.
Gera grafo_IMC.json e vertices_IMC.json.

Peso da aresta: mesma fórmula do backend (backend/src/engine/peso.py)
    z_d  = ln(1 + x_d) / ln(1 + M_d)
    peso = soma(ALFAS[d] * z_d)
"""
import csv
import json
import math
import os
import random
import sys
import time
from collections import Counter, defaultdict, deque

random.seed(42)

# configuração
PASTA_SCRIPT = os.path.dirname(os.path.abspath(__file__))

CONFIG = {
    'arquivos': {
        'saida': 'dataset_saida_IMC.csv',
        'unifei': 'dataset_completo_UNIFEI.csv',
        'entrada': 'dataset_entrada_IMC.csv',
        'atividades': 'dataset_atividades_IMC.csv',
    },
    'colunas_saida': {
        'id1': 'id pesquisador 1', 'id2': 'id pesquisador 2',
        'nome1': 'nome do pesquisador 1', 'nome2': 'nome do pesquisador 2',
        'inst1': 'instituto pesquisador 1', 'inst2': 'instituto pesquisador 2',
        'tipo': 'tipo de relacao', 'vetor': 'vetor contagem', 'bruto': 'vetor bruto',
    },
    'colunas_unifei': {'id': 'pesquisador_id', 'nome': 'nome', 'instituto': 'instituto', 'area': 'area'},
    'colunas_entrada': {'id': 'pesquisador_id', 'nome': 'nome do pesquisador',
                        'instituto': 'instituto', 'area': 'area de trabalho', 'vetor': 'vetor contagem'},
    'colunas_atividades': {'id': 'id_atividade', 'participantes': 'ids_participantes'},
    'json_grafo': 'grafo_IMC.json',
    'json_vertices': 'vertices_IMC.json',
}

DIMENSOES = ['ART', 'PRJ', 'ORI', 'BAN', 'PTT']
# peso de cada dimensão (igual ao backend/src/config.py). None = peso simples
ALFAS = {'ART': 0.40, 'PRJ': 0.20, 'ORI': 0.20, 'BAN': 0.05, 'PTT': 0.15}

INSTITUTOS_UNIFEI = ['IFQ', 'IESTI', 'IEPG', 'IRN', 'IEM', 'IEDU', 'ISEE', 'ICT', 'ICPA', 'IEI', 'UNIFEI - PA']
COMP, MAT, INDEF = 'Computação', 'Matemática', 'Indefinido'
REGRAS_AREA = {COMP: ['ciência da computação'], MAT: ['matemática', 'probabilidade e estatística']}

# força a área de alguém, ex: {"2053076": ["Matemática"]}
CLASSIFICACAO_MANUAL = {}

PARES_UNICOS_ESPERADOS = 1898   # valor do enunciado (CSVs antigos)
# M da versão antiga dos CSVs, só pra conferir os valores do enunciado
M_DO_PROMPT = [33, 12, 5, 40, 17]
TOP = 10
LARG_NOME = 35


# impressão
def cabecalho(titulo):
    print('\n' + '=' * 20 + f' {titulo} ' + '=' * 20)


def sub(titulo):
    print(f'\n--- {titulo} ---')


def corta(nome, n=LARG_NOME):
    return nome if len(nome) <= n else nome[:n - 1] + '…'


def tabela(linhas, colunas, alinhamento):
    """tabela alinhada, alinhamento 'l' ou 'r' por coluna"""
    larg = [max(len(str(c)), *(len(str(l[i])) for l in linhas)) if linhas else len(str(c))
            for i, c in enumerate(colunas)]
    fmt = lambda valores: ' | '.join(str(v).ljust(w) if a == 'l' else str(v).rjust(w)
                                     for v, w, a in zip(valores, larg, alinhamento))
    print(fmt(colunas))
    print('-+-'.join('-' * w for w in larg))
    for l in linhas:
        print(fmt(l))


def status(ok, texto):
    print(f"  [{'OK' if ok else 'FALHOU'}] {texto}")


# etapa 0: leitura
def achar_pasta_csv():
    if len(sys.argv) > 1:
        return sys.argv[1]
    if os.path.exists(os.path.join(PASTA_SCRIPT, CONFIG['arquivos']['saida'])):
        return PASTA_SCRIPT
    return os.path.join(PASTA_SCRIPT, '..', 'backend', 'data', 'raw')


def ler_csv(pasta, chave):
    with open(os.path.join(pasta, CONFIG['arquivos'][chave]), encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def mostrar_estrutura(dados):
    cabecalho('ESTRUTURA DOS CSVs')
    for chave, linhas in dados.items():
        print(f"\n{CONFIG['arquivos'][chave]}: {len(linhas)} linhas")
        print('  colunas: ' + ', '.join(linhas[0].keys() if linhas else []))


def vetor(texto):
    """'[1, 0, 2, 0, 0]' -> lista de 5 inteiros (inválido vira zeros)"""
    try:
        v = json.loads(texto) if texto and texto.strip() else None
    except json.JSONDecodeError:
        v = None
    return [int(x) for x in v] if isinstance(v, list) and len(v) == 5 else [0] * 5


# etapa 1: peso
def pesos_definidos():
    return all(ALFAS.get(d) is not None for d in DIMENSOES)


def referencias_por_dimensao(arestas):
    maiores = [0] * 5
    for a in arestas.values():
        maiores = [max(m, x) for m, x in zip(maiores, a['vetor'])]
    return maiores


def calcular_peso(vetor_contagem, maiores):
    if not pesos_definidos():
        return float(sum(vetor_contagem))
    total = 0.0
    for d, x, m in zip(DIMENSOES, vetor_contagem, maiores):
        if m > 0:
            total += ALFAS[d] * math.log1p(x) / math.log1p(m)
    return round(total, 6)


def arestas_unicas(linhas):
    """chave = par ordenado; duplicata não soma, só confere o vetor"""
    c = CONFIG['colunas_saida']
    arestas, conflitos, auto = {}, 0, 0
    for l in linhas:
        a, b = l[c['id1']].strip(), l[c['id2']].strip()
        if a == b:
            auto += 1
            continue
        chave = (min(a, b), max(a, b))
        v = vetor(l[c['vetor']])
        if chave in arestas:
            if arestas[chave]['vetor'] != v:
                conflitos += 1
            continue
        arestas[chave] = {'vetor': v, 'tipo': l[c['tipo']], 'bruto': l[c['bruto']]}
    return arestas, conflitos, auto


# etapa 1: vértices
def areas_de(texto):
    return [a.strip() for a in (texto or '').split(';') if a.strip()]


def classificar_imc(pid, areas):
    if pid in CLASSIFICACAO_MANUAL:
        return list(CLASSIFICACAO_MANUAL[pid])
    t = ' '.join(areas).lower()
    grupos = [g for g, chaves in REGRAS_AREA.items() if any(k in t for k in chaves)]
    return grupos or [INDEF]


def montar_vertices(unifei, entrada, saida):
    """UNIFEI vem do dataset_completo, o resto do dataset_entrada"""
    cu, ce, cs = CONFIG['colunas_unifei'], CONFIG['colunas_entrada'], CONFIG['colunas_saida']
    v = {}
    for l in unifei:
        v[l[cu['id']]] = {'nome': l[cu['nome']], 'instituto': l[cu['instituto']], 'areas': areas_de(l[cu['area']])}
    for l in entrada:
        pid = l[ce['id']]
        if pid not in v:
            v[pid] = {'nome': l[ce['nome']], 'instituto': l[ce['instituto']], 'areas': areas_de(l[ce['area']])}
    for l in saida:  # todo id de aresta precisa ter atributo
        for k in ('1', '2'):
            pid = l[cs['id' + k]]
            if pid not in v:
                v[pid] = {'nome': l[cs['nome' + k]], 'instituto': l[cs['inst' + k]], 'areas': []}
    for pid, a in v.items():
        a['grupo_imc'] = classificar_imc(pid, a['areas']) if a['instituto'] == 'IMC' else []
    return v


def montar_adjacencia(arestas, vertices, maiores):
    adj = {pid: {} for pid, a in vertices.items() if a['instituto'] == 'IMC'}
    for (a, b), info in arestas.items():
        p = calcular_peso(info['vetor'], maiores)
        adj.setdefault(a, {})[b] = p
        adj.setdefault(b, {})[a] = p
    return adj


def salvar_json(obj, nome):
    with open(os.path.join(PASTA_SCRIPT, nome), 'w', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, sort_keys=True)


def carregar_json(nome):
    with open(os.path.join(PASTA_SCRIPT, nome), encoding='utf-8') as f:
        return json.load(f)


# utilidades de grafo
def subgrafo(adj, ids):
    ids = set(ids)
    return {u: {v: w for v, w in adj[u].items() if v in ids} for u in adj if u in ids}


def contar_arestas(adj):
    return sum(len(n) for n in adj.values()) // 2


def densidade(adj):
    n = len(adj)
    return 2 * contar_arestas(adj) / (n * (n - 1)) if n > 1 else 0.0


def bfs_distancias(adj, origem):
    dist = {origem: 0}
    fila = deque([origem])
    while fila:
        u = fila.popleft()
        for v in adj[u]:
            if v not in dist:
                dist[v] = dist[u] + 1
                fila.append(v)
    return dist


def componentes(adj):
    vistos, comps = set(), []
    for s in sorted(adj):
        if s not in vistos:
            c = set(bfs_distancias(adj, s))
            vistos |= c
            comps.append(c)
    return sorted(comps, key=len, reverse=True)


# pergunta 1: centralidade
def grau(adj):
    return {u: len(n) for u, n in adj.items()}


def forca(adj):
    return {u: sum(n.values()) for u, n in adj.items()}


def intermediacao_brandes(adj):
    """Brandes sem peso, normalizado por 2/((n-1)(n-2))"""
    cb = dict.fromkeys(adj, 0.0)
    for s in adj:
        pilha, pred = [], defaultdict(list)
        sigma = dict.fromkeys(adj, 0)
        dist = dict.fromkeys(adj, -1)
        sigma[s], dist[s] = 1, 0
        fila = deque([s])
        while fila:
            u = fila.popleft()
            pilha.append(u)
            for v in adj[u]:
                if dist[v] < 0:
                    dist[v] = dist[u] + 1
                    fila.append(v)
                if dist[v] == dist[u] + 1:
                    sigma[v] += sigma[u]
                    pred[v].append(u)
        delta = dict.fromkeys(adj, 0.0)
        while pilha:
            w = pilha.pop()
            for u in pred[w]:
                delta[u] += sigma[u] / sigma[w] * (1 + delta[w])
            if w != s:
                cb[w] += delta[w]
    n = len(adj)
    fator = 2 / ((n - 1) * (n - 2)) if n > 2 else 0.0
    return {u: c / 2 * fator for u, c in cb.items()}


def proximidade_wf(adj):
    """Wasserman-Faust: ((r-1)/(n-1)) * ((r-1)/soma_dist)"""
    n = len(adj)
    res = {}
    for u in adj:
        d = bfs_distancias(adj, u)
        r, soma = len(d), sum(d.values())
        res[u] = ((r - 1) / (n - 1)) * ((r - 1) / soma) if soma > 0 and n > 1 else 0.0
    return res


def posicoes(valores, candidatos):
    ordem = sorted(candidatos, key=lambda u: (-valores[u], u))
    return {u: i + 1 for i, u in enumerate(ordem)}


def centralidades(adj):
    return {'Grau': grau(adj), 'Força': forca(adj),
            'Intermediação': intermediacao_brandes(adj), 'Proximidade': proximidade_wf(adj)}


def ranking_combinado(medidas, candidatos):
    pos = {nome: posicoes(m, candidatos) for nome, m in medidas.items()}
    return {u: sum(p[u] for p in pos.values()) / len(pos) for u in candidatos}


def rotulo(vertices, u):
    a = vertices[u]
    curto = {COMP: 'Comp', MAT: 'Mat', INDEF: 'Indef'}
    return a['instituto'] if a['instituto'] != 'IMC' else 'IMC/' + '+'.join(curto[g] for g in a['grupo_imc'])


def fmt_valor(nome, x):
    return str(int(x)) if nome == 'Grau' else f'{x:.6f}' if nome == 'Força' else f'{x:.4f}'


def pergunta1(grafos, vertices):
    cabecalho('PERGUNTA 1 — CENTRALIDADE')
    resultados = {}
    for nome_g, adj in grafos.items():
        if nome_g == 'G_UNIFEI':
            continue
        sub(f'{nome_g}: {len(adj)} vértices, {contar_arestas(adj)} arestas')
        medidas = centralidades(adj)
        candidatos = [u for u in adj if vertices[u]['instituto'] != 'EXT']
        for nome_m, m in medidas.items():
            print(f'\n{nome_m} (top {TOP})')
            top = sorted(candidatos, key=lambda u: (-m[u], u))[:TOP]
            tabela([(i + 1, corta(vertices[u]['nome']), rotulo(vertices, u), fmt_valor(nome_m, m[u]))
                    for i, u in enumerate(top)], ['#', 'Nome', 'Inst/Grupo', 'Valor'], 'rllr')
        comb = ranking_combinado(medidas, candidatos)
        print(f'\nRanking combinado (média das posições, top {TOP})')
        top = sorted(candidatos, key=lambda u: (comb[u], u))[:TOP]
        tabela([(i + 1, corta(vertices[u]['nome']), rotulo(vertices, u), f'{comb[u]:.2f}')
                for i, u in enumerate(top)], ['#', 'Nome', 'Inst/Grupo', 'Pos. média'], 'rllr')
        lider_g = max(candidatos, key=lambda u: medidas['Grau'][u])
        lider_b = max(candidatos, key=lambda u: medidas['Intermediação'][u])
        print(f"\nInterpretação: em {nome_g}, {vertices[lider_g]['nome']} tem mais colaboradores diretos "
              f"(grau {medidas['Grau'][lider_g]}); {vertices[lider_b]['nome']} é quem mais aparece nos "
              f"caminhos mais curtos entre outros pesquisadores (intermediação "
              f"{medidas['Intermediação'][lider_b]:.4f}), ou seja, liga grupos que de outra forma ficariam "
              f"distantes. Força alta indica parcerias intensas, não só numerosas; proximidade alta indica "
              f"quem alcança a rede inteira em poucos passos.")
        resultados[nome_g] = {'medidas': medidas, 'comb': comb, 'top': top}
    return resultados


# pergunta 2: pontes
def tarjan_iterativo(adj):
    """pontos de articulação e pontes (DFS iterativa)"""
    desc, low, pai = {}, {}, {}
    articulacoes, pontes = set(), []
    tempo = 0
    for raiz in sorted(adj):
        if raiz in desc:
            continue
        desc[raiz] = low[raiz] = tempo
        tempo += 1
        pai[raiz] = None
        filhos_raiz = 0
        pilha = [(raiz, iter(adj[raiz]))]
        while pilha:
            u, it = pilha[-1]
            avancou = False
            for v in it:
                if v not in desc:
                    pai[v] = u
                    desc[v] = low[v] = tempo
                    tempo += 1
                    if u == raiz:
                        filhos_raiz += 1
                    pilha.append((v, iter(adj[v])))
                    avancou = True
                    break
                if v != pai[u]:
                    low[u] = min(low[u], desc[v])
            if avancou:
                continue
            pilha.pop()
            p = pai[u]
            if p is not None:
                low[p] = min(low[p], low[u])
                if low[u] > desc[p]:
                    pontes.append((p, u))
                if p != raiz and low[u] >= desc[p]:
                    articulacoes.add(p)
        if filhos_raiz > 1:
            articulacoes.add(raiz)
    return articulacoes, pontes


def pontes_comp_mat(g_imc, vertices):
    grupos = lambda u: set(vertices[u]['grupo_imc'])
    contagem = Counter()
    for u in g_imc:
        for v in g_imc[u]:
            if u < v:
                gu, gv = grupos(u), grupos(v)
                if COMP in gu and COMP in gv and MAT not in gu | gv:
                    contagem['Comp-Comp'] += 1
                elif MAT in gu and MAT in gv and COMP not in gu | gv:
                    contagem['Mat-Mat'] += 1
                elif (COMP in gu and MAT in gv) or (MAT in gu and COMP in gv):
                    contagem['Comp-Mat'] += 1
                else:
                    contagem['Outras (Indefinido)'] += 1
    pontes = []
    for u in g_imc:
        gu = grupos(u)
        if not gu & {COMP, MAT}:
            continue
        dupla = {COMP, MAT} <= gu
        nc = sum(COMP in grupos(v) for v in g_imc[u])
        nm = sum(MAT in grupos(v) for v in g_imc[u])
        oposto = {MAT} if COMP in gu else {COMP}
        if dupla:
            # para quem está nos dois grupos, "cruzada" = vizinho que está em só um dos lados
            cruz = [v for v in g_imc[u] if grupos(v) & {COMP, MAT} and not {COMP, MAT} <= grupos(v)]
        else:
            cruz = [v for v in g_imc[u] if grupos(v) & oposto]
        if not (dupla or cruz):
            continue
        tipo = 'ambos' if dupla and cruz else 'dupla área' if dupla else 'conector'
        pontes.append({'id': u, 'tipo': tipo, 'nc': nc, 'nm': nm, 'n_cruz': len(cruz),
                       'peso_cruz': sum(g_imc[u][v] for v in cruz),
                       'indice': len(cruz) / len(g_imc[u]) if g_imc[u] else 0.0})
    pontes.sort(key=lambda p: (-p['peso_cruz'], p['id']))
    return pontes, contagem


def pontes_institutos(g_unifei, vertices):
    pontes, matriz = [], {i: {'arestas': 0, 'peso': 0.0, 'por_docente': Counter()} for i in INSTITUTOS_UNIFEI}
    for u in g_unifei:
        if vertices[u]['instituto'] != 'IMC':
            continue
        fora = [v for v in g_unifei[u] if vertices[v]['instituto'] in INSTITUTOS_UNIFEI]
        for v in fora:
            i = vertices[v]['instituto']
            matriz[i]['arestas'] += 1
            matriz[i]['peso'] += g_unifei[u][v]
            matriz[i]['por_docente'][u] += 1
        if fora:
            insts = sorted({vertices[v]['instituto'] for v in fora})
            pontes.append({'id': u, 'insts': insts, 'n': len(fora), 'peso': sum(g_unifei[u][v] for v in fora)})
    pontes.sort(key=lambda p: (-len(p['insts']), -p['peso'], p['id']))
    return pontes, matriz


def pergunta2(grafos, adj_total, vertices):
    cabecalho('PERGUNTA 2 — PONTES')
    g_imc, g_unifei = grafos['G_IMC'], grafos['G_UNIFEI']
    nome = lambda u: corta(vertices[u]['nome'])

    sub('Definição A — ponte Computação <-> Matemática (dentro do IMC)')
    pa, contagem = pontes_comp_mat(g_imc, vertices)
    tabela([(i + 1, nome(p['id']), p['tipo'], p['nc'], p['nm'], p['n_cruz'], f"{p['peso_cruz']:.6f}",
             f"{p['indice']:.4f}") for i, p in enumerate(pa)],
           ['#', 'Nome', 'Tipo', 'Viz.Comp', 'Viz.Mat', 'Cruzadas', 'Peso cruzado', 'Índice'], 'rllrrrrr')
    total = sum(contagem.values())
    print('\nArestas do G_IMC por tipo:')
    for k in ['Comp-Comp', 'Mat-Mat', 'Comp-Mat', 'Outras (Indefinido)']:
        print(f'  {k.ljust(22)} {str(contagem[k]).rjust(4)}  ({100 * contagem[k] / total:.1f}%)')
    print(f"  Porcentagem de arestas cruzadas (Comp-Mat): {100 * contagem['Comp-Mat'] / total:.1f}%")

    sub('Definição B — ponte IMC <-> outros institutos da UNIFEI (sem EXT)')
    pb, matriz = pontes_institutos(g_unifei, vertices)
    tabela([(i + 1, nome(p['id']), len(p['insts']), ', '.join(p['insts']), p['n'], f"{p['peso']:.6f}")
            for i, p in enumerate(pb)],
           ['#', 'Nome', 'Nº inst.', 'Institutos', 'Colab.', 'Peso'], 'rlrlrr')
    print('\nMatriz IMC x instituto')
    linhas = []
    for i in sorted(INSTITUTOS_UNIFEI, key=lambda i: -matriz[i]['arestas']):
        m = matriz[i]
        top = m['por_docente'].most_common(1)
        linhas.append((i, m['arestas'], f"{m['peso']:.6f}",
                       f"{nome(top[0][0])} ({top[0][1]})" if top else '-'))
    tabela(linhas, ['Instituto', 'Arestas', 'Soma pesos', 'Docente IMC com mais ligações'], 'lrrl')

    sub(f'TOP {TOP} docentes do IMC por ligações com EXT')
    ext = []
    for u in adj_total:
        if vertices[u]['instituto'] == 'IMC':
            viz = [v for v in adj_total[u] if vertices[v]['instituto'] == 'EXT']
            ext.append((u, len(viz), sum(adj_total[u][v] for v in viz)))
    ext.sort(key=lambda t: (-t[1], -t[2], t[0]))
    tabela([(i + 1, nome(u), n, f'{p:.6f}') for i, (u, n, p) in enumerate(ext[:TOP])],
           ['#', 'Nome', 'Colab. EXT', 'Peso'], 'rlrr')

    sub('Complemento estrutural — Tarjan (iterativo)')
    estrutura = {}
    for g_nome in ('G_UNIFEI', 'G_IMC'):
        art, br = tarjan_iterativo(grafos[g_nome])
        estrutura[g_nome] = (art, br)
        print(f'\n{g_nome}: {len(art)} pontos de articulação, {len(br)} arestas-ponte')
        print('  Articulações: ' + (', '.join(sorted(vertices[u]['nome'] for u in art)) or '-'))
        print('  Arestas-ponte:')
        for a, b in sorted(br, key=lambda e: (vertices[e[0]]['nome'], vertices[e[1]]['nome'])):
            print(f"    {corta(vertices[a]['nome'])} — {corta(vertices[b]['nome'])}")

    ids_a, ids_b = {p['id'] for p in pa}, {p['id'] for p in pb}
    art_todas = estrutura['G_UNIFEI'][0] | estrutura['G_IMC'][0]
    insub = sorted((ids_a | ids_b) & art_todas, key=lambda u: vertices[u]['nome'])
    print('\nPontes "insubstituíveis" (ponte pela def. A ou B e ponto de articulação):')
    tabela([(nome(u), 'A' if u in ids_a else '-', 'B' if u in ids_b else '-',
             'sim' if u in estrutura['G_UNIFEI'][0] else '-', 'sim' if u in estrutura['G_IMC'][0] else '-')
            for u in insub], ['Nome', 'Def.A', 'Def.B', 'Art. G_UNIFEI', 'Art. G_IMC'], 'lllll')
    return {'A': pa, 'B': pb, 'contagem': contagem, 'matriz': matriz, 'estrutura': estrutura,
            'insubstituiveis': insub, 'ext': ext}


# pergunta 3: Louvain
def modularidade(adj, comunidade):
    m2 = sum(sum(n.values()) for n in adj.values())  # 2m
    if m2 == 0:
        return 0.0
    interno, grau_com = defaultdict(float), defaultdict(float)
    for u, viz in adj.items():
        grau_com[comunidade[u]] += sum(viz.values())
        for v, w in viz.items():
            if comunidade[u] == comunidade[v]:
                interno[comunidade[u]] += w  # cada aresta interna conta 2x
    return sum(interno[c] / m2 - (grau_com[c] / m2) ** 2 for c in grau_com)


def louvain_fase1(adj):
    """move os nós pra comunidade vizinha de maior ganho"""
    com = {u: u for u in adj}
    # laço do supernó já guarda 2x o peso interno
    k = {u: sum(adj[u].values()) for u in adj}
    m2 = sum(k.values())
    tot = dict(k)
    if m2 == 0:
        return com, False
    melhorou_alguma = False
    while True:
        mudou = False
        ordem = list(adj)
        random.shuffle(ordem)
        for u in ordem:
            c_atual = com[u]
            pesos_c = defaultdict(float)
            for v, w in adj[u].items():
                if v != u:
                    pesos_c[com[v]] += w
            tot[c_atual] -= k[u]
            melhor, ganho_melhor = c_atual, pesos_c.get(c_atual, 0.0) - tot[c_atual] * k[u] / m2
            for c, w in pesos_c.items():
                ganho = w - tot[c] * k[u] / m2
                if ganho > ganho_melhor + 1e-12:
                    melhor, ganho_melhor = c, ganho
            tot[melhor] += k[u]
            if melhor != c_atual:
                com[u] = melhor
                mudou = melhorou_alguma = True
        if not mudou:
            break
    return com, melhorou_alguma


def louvain_agregar(adj, com):
    """monta o grafo de supernós"""
    novo = defaultdict(lambda: defaultdict(float))
    for u, viz in adj.items():
        novo[com[u]]  # garante isolados
        for v, w in viz.items():
            novo[com[u]][com[v]] += w
    return {c: dict(n) for c, n in novo.items()}


def louvain(adj):
    particao = {u: u for u in adj}
    atual = {u: dict(n) for u, n in adj.items()}
    while True:
        com, melhorou = louvain_fase1(atual)
        if not melhorou:
            break
        particao = {u: com[particao[u]] for u in particao}
        atual = louvain_agregar(atual, com)
    # renumera comunidades por tamanho
    tam = Counter(particao.values())
    ids = {c: i + 1 for i, (c, _) in enumerate(sorted(tam.items(), key=lambda t: (-t[1], str(t[0]))))}
    return {u: ids[c] for u, c in particao.items()}


def resumo_comunidades(adj, com):
    membros = defaultdict(list)
    for u, c in com.items():
        membros[c].append(u)
    res = []
    for c in sorted(membros):
        ms = set(membros[c])
        internas = sum(1 for u in ms for v in adj[u] if v in ms) // 2
        externas = sum(1 for u in ms for v in adj[u] if v not in ms)
        forca_int = {u: sum(w for v, w in adj[u].items() if v in ms) for u in ms}
        n = len(ms)
        res.append({'id': c, 'membros': ms, 'lider': max(sorted(ms), key=lambda u: forca_int[u]),
                    'densidade': 2 * internas / (n * (n - 1)) if n > 1 else 0.0,
                    'internas': internas, 'externas': externas})
    return res


def pergunta3(grafos, vertices, pontes):
    cabecalho('PERGUNTA 3 — COMUNIDADES (COMPUTAÇÃO E MATEMÁTICA)')
    ids_ponte = {p['id'] for p in pontes['A']} | {p['id'] for p in pontes['B']}
    resultados = {}
    for g_nome in ('G_COMP', 'G_MAT'):
        adj = grafos[g_nome]
        sub(f'{g_nome}: {len(adj)} docentes, {contar_arestas(adj)} arestas, densidade {densidade(adj):.4f}')
        comps = componentes(adj)
        isolados = [u for u in adj if not adj[u]]
        print(f"Componentes conexas: {len(comps)}  tamanhos: {[len(c) for c in comps]}")
        print('Isolados (grau 0 no grupo): ' + (', '.join(sorted(vertices[u]['nome'] for u in isolados)) or '-'))
        com = louvain(adj)
        q = modularidade(adj, com)
        print(f'Louvain: {len(set(com.values()))} comunidades, modularidade Q = {q:.4f}')
        res = resumo_comunidades(adj, com)
        for r in res:
            ponte = [vertices[u]['nome'] for u in r['membros'] if u in ids_ponte]
            print(f"\n  Comunidade {r['id']} — {len(r['membros'])} membros | líder: "
                  f"{vertices[r['lider']]['nome']} | densidade interna {r['densidade']:.4f} | "
                  f"arestas internas {r['internas']} | externas {r['externas']}")
            print('    Membros: ' + ', '.join(sorted(vertices[u]['nome'] for u in r['membros'])))
            print('    Docentes ponte (P2) nela: ' + (', '.join(sorted(ponte)) or '-'))
        maior = max(res, key=lambda r: len(r['membros']))
        frac = len(maior['membros']) / len(adj)
        perfil = 'fragmentada' if len(comps) > 1 or q > 0.4 else 'coesa'
        print(f"\nInterpretação: {g_nome} é {perfil} — {len(comps)} componente(s), "
              f"{len(isolados)} isolado(s), Q = {q:.2f}. A maior comunidade (liderada por "
              f"{vertices[maior['lider']]['nome']}) reúne {100 * frac:.0f}% do grupo"
              f"{', o que indica um grupo dominante' if frac >= 0.4 else '; não há um grupo dominante'}. "
              f"As comunidades com docentes-ponte são as que conectam o grupo ao restante do IMC e da UNIFEI.")
        resultados[g_nome] = {'com': com, 'q': q, 'comps': comps, 'isolados': isolados, 'res': res}
    return resultados


# validações
def conferir_atividades(atividades, arestas, n=3):
    c = CONFIG['colunas_atividades']
    part = {l[c['id']]: set(p for p in l[c['participantes']].split(';') if p) for l in atividades}
    escolhidas = sorted(arestas, key=lambda k: -sum(arestas[k]['vetor']))[:n]
    resultado = []
    for a, b in escolhidas:
        ids = [x for lista in json.loads(arestas[(a, b)]['bruto']) for x in lista]
        ok = all(i in part and a in part[i] and b in part[i] for i in ids)
        resultado.append(((a, b), len(ids), ok))
    return resultado


def validar(adj, vertices, arestas, conflitos, auto, maiores, intermed, louv, atividades):
    cabecalho('VALIDAÇÕES')
    n_ar = len(arestas)
    status(n_ar == PARES_UNICOS_ESPERADOS,
           f'pares únicos = {n_ar} (prompt cita {PARES_UNICOS_ESPERADOS}; '
           'a diferença vem dos CSVs mais novos da mineração)' if n_ar != PARES_UNICOS_ESPERADOS
           else f'pares únicos = {n_ar}')
    status(conflitos == 0, f'duplicatas com o mesmo vetor (conflitos: {conflitos}); laços removidos: {auto}')
    sim = all(adj[b].get(a) == w for a in adj for b, w in adj[a].items())
    status(sim, 'simetria adj[A][B] == adj[B][A]')
    status(all(a not in adj[a] for a in adj), 'sem laços A->A')
    status(sum(len(v) for v in adj.values()) == 2 * contar_arestas(adj) and contar_arestas(adj) == n_ar,
           f'soma dos graus = 2 x arestas ({sum(len(v) for v in adj.values())} = 2 x {contar_arestas(adj)})')
    status(all(u in vertices for u in adj), 'todo ID da adjacência existe em vertices_IMC.json')
    if pesos_definidos():
        # a fórmula é conferida com os M antigos, os pesos usam os M atuais
        for v, esperado in (([2, 0, 1, 1, 1], 0.247292), ([1, 0, 0, 0, 0], 0.078625), ([0, 0, 0, 1, 0], 0.009333)):
            p = calcular_peso(v, M_DO_PROMPT)
            status(abs(p - esperado) < 1e-6, f'peso({v}) com M do prompt = {p:.6f} (esperado {esperado})')
        if maiores != M_DO_PROMPT:
            print(f'       obs.: nos CSVs atuais M = {maiores}, então os pesos gravados são outros '
                  f'(ex.: [2,0,1,1,1] -> {calcular_peso([2, 0, 1, 1, 1], maiores):.6f})')
    for g, b in intermed.items():
        status(all(0 <= x <= 1 for x in b.values()), f'intermediação entre 0 e 1 ({g})')
    for g, q in louv.items():
        status(-0.5 <= q <= 1, f'modularidade entre -0.5 e 1 ({g}: {q:.4f})')
    for (a, b), n, ok in conferir_atividades(atividades, arestas):
        status(ok, f"{n} atividades do vetor bruto contêm {corta(vertices[a]['nome'], 25)} e "
                   f"{corta(vertices[b]['nome'], 25)} em ids_participantes")


# principal
def main():
    t0 = time.time()
    pasta = achar_pasta_csv()
    dados = {k: ler_csv(pasta, k) for k in CONFIG['arquivos']}
    mostrar_estrutura(dados)

    # etapa 1: CSV -> JSON
    cabecalho('ETAPA 1 — CSV -> JSON')
    arestas, conflitos, auto = arestas_unicas(dados['saida'])
    maiores = referencias_por_dimensao(arestas)
    if not pesos_definidos():
        print('\n' + '!' * 70 + '\n!!! AVISO: ALFAS tem valor None — os pesos do artigo NÃO foram aplicados.'
              '\n!!! Usando peso simples = soma do vetor contagem.\n' + '!' * 70)
    else:
        print('Fórmula: peso = Σ α_d · ln(1 + x_d) / ln(1 + M_d)')
        print('  α = ' + ', '.join(f'{d} {ALFAS[d]:.2f}' for d in DIMENSOES))
        print('  M = ' + ', '.join(f'{d} {m}' for d, m in zip(DIMENSOES, maiores)) + '  (maior valor de cada dimensão)')
        print('  Peso de 1 atividade isolada: ' +
              ', '.join(f'{d} {calcular_peso([int(i == j) for i in range(5)], maiores):.6f}'
                        for j, d in enumerate(DIMENSOES)))
    print('Exemplos:')
    for v in ([1, 0, 0, 0, 0], [0, 0, 0, 1, 0], [2, 0, 1, 1, 1], [6, 0, 0, 18, 8]):
        print(f'  {v} -> {calcular_peso(v, maiores):.6f}')

    vertices = montar_vertices(dados['unifei'], dados['entrada'], dados['saida'])
    adj = montar_adjacencia(arestas, vertices, maiores)
    vertices = {u: vertices[u] for u in adj}  # só quem está na rede (inclui IMC isolado)
    salvar_json(adj, CONFIG['json_grafo'])
    salvar_json(vertices, CONFIG['json_vertices'])
    print(f"\nGravados: {CONFIG['json_grafo']} e {CONFIG['json_vertices']} em {PASTA_SCRIPT}")

    # recarrega do JSON
    adj = carregar_json(CONFIG['json_grafo'])
    vertices = carregar_json(CONFIG['json_vertices'])

    inst = Counter('IMC' if a['instituto'] == 'IMC' else 'EXT' if a['instituto'] == 'EXT' else 'UNIFEI'
                   for a in vertices.values())
    imc = [u for u, a in vertices.items() if a['instituto'] == 'IMC']
    sub('Resumo')
    print(f"Vértices: {len(adj)}  (IMC {inst['IMC']}, outros institutos UNIFEI {inst['UNIFEI']}, EXT {inst['EXT']})")
    print(f'Arestas únicas: {contar_arestas(adj)}   densidade: {densidade(adj):.6f}')
    gc = Counter()
    for u in imc:
        g = set(vertices[u]['grupo_imc'])
        gc[COMP] += COMP in g
        gc[MAT] += MAT in g
        gc['dois'] += {COMP, MAT} <= g
        gc[INDEF] += INDEF in g
    print(f"IMC — Computação: {gc[COMP]}, Matemática: {gc[MAT]}, nos dois grupos: {gc['dois']}, "
          f"Indefinido: {gc[INDEF]}")
    print('Docentes Indefinido (use CLASSIFICACAO_MANUAL para corrigir):')
    for u in sorted(imc, key=lambda u: vertices[u]['nome']):
        if INDEF in vertices[u]['grupo_imc']:
            print(f"  {u.ljust(10)} {vertices[u]['nome'].ljust(36)} áreas: {'; '.join(vertices[u]['areas']) or '(vazio)'}")
    print('Arestas por tipo de relação:')
    tipos = Counter(a['tipo'] for a in arestas.values())
    for t, n in tipos.most_common():
        print(f'  {t.ljust(18)} {str(n).rjust(5)}')

    # subgrafos
    grafos = {
        'G_TOTAL': adj,
        'G_UNIFEI': subgrafo(adj, [u for u in adj if vertices[u]['instituto'] != 'EXT']),
        'G_IMC': subgrafo(adj, imc),
        'G_COMP': subgrafo(adj, [u for u in imc if COMP in vertices[u]['grupo_imc']]),
        'G_MAT': subgrafo(adj, [u for u in imc if MAT in vertices[u]['grupo_imc']]),
    }

    r1 = pergunta1(grafos, vertices)
    r2 = pergunta2(grafos, adj, vertices)
    r3 = pergunta3(grafos, vertices, r2)

    validar(adj, vertices, arestas, conflitos, auto, maiores,
            {g: r['medidas']['Intermediação'] for g, r in r1.items()},
            {g: r['q'] for g, r in r3.items()}, dados['atividades'])

    # respostas
    cabecalho('RESPOSTAS FINAIS')
    n = lambda u: vertices[u]['nome']
    print('\nPergunta 1 — Quem é central?')
    for g in ('G_TOTAL', 'G_IMC', 'G_COMP', 'G_MAT'):
        print(f"  {g}: {', '.join(n(u) for u in r1[g]['top'][:3])} (top 3 do ranking combinado).")
    print('\nPergunta 2 — Quem faz ponte?')
    c = r2['contagem']
    print(f"  Def. A: {len(r2['A'])} docentes; mais forte: {n(r2['A'][0]['id'])}. "
          f"Só {100 * c['Comp-Mat'] / sum(c.values()):.1f}% das arestas do IMC cruzam Comp-Mat.")
    print(f"  Def. B: {len(r2['B'])} docentes; mais amplo: {n(r2['B'][0]['id'])} "
          f"({len(r2['B'][0]['insts'])} institutos).")
    print(f"  Mais ligado a externos: {n(r2['ext'][0][0])} ({r2['ext'][0][1]} colaboradores EXT).")
    print(f"  Insubstituíveis (ponte + articulação): {', '.join(n(u) for u in r2['insubstituiveis']) or '-'}.")
    print('\nPergunta 3 — Como se organizam Computação e Matemática?')
    for g in ('G_COMP', 'G_MAT'):
        r = r3[g]
        maior = max(r['res'], key=lambda x: len(x['membros']))
        print(f"  {g}: {len(r['res'])} comunidades (Q = {r['q']:.2f}), {len(r['comps'])} componente(s), "
              f"{len(r['isolados'])} isolado(s); maior comunidade liderada por {n(maior['lider'])}.")

    print(f'\nTempo total de execução: {time.time() - t0:.2f} s')


if __name__ == '__main__':
    main()
