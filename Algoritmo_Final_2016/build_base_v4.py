# build_base_v4.py - base completa e recorte 2016-2026 a partir do ATIVIDADES (zip 012783cd)
# Rode sem argumentos (botão play): gera dataset_IMC_v4.xlsx e dataset_IMC_2016_2026.xlsx.
# (MATÉRIA: projeção de grafo bipartido pessoa-atividade; grafo não direcionado ponderado)
import collections
import itertools
import json
import os

import pandas as pd

PASTA = os.path.dirname(os.path.abspath(__file__))
BASES = [
    (2016, 2026, 'dataset_IMC_2016_2026.xlsx'),
]


def construir(ano_ini, ano_fim, arquivo_saida):
    DIM = ['ART', 'PRJ', 'ORI', 'BAN', 'PTT']          # ordem do vetor contagem
    a = pd.read_csv(os.path.join(PASTA, 'dataset_atividades_IMC.csv'), dtype=str, encoding='utf-8-sig')
    n_total = len(a)
    ano = pd.to_numeric(a['ano'], errors='coerce')
    if ano_ini is not None:
        a = a[ano >= ano_ini]
    if ano_fim is not None:
        a = a[pd.to_numeric(a['ano'], errors='coerce') <= ano_fim]
    print(f'atividades: {n_total} no arquivo | {len(a)} após o recorte de ano')
    cad = pd.read_csv(os.path.join(PASTA, 'dataset_entrada_IMC.csv'), dtype=str, encoding='utf-8-sig')
    cad_d = {r['pesquisador_id']: r for _, r in cad.iterrows()}

    nome, inst = {}, {}
    cont = collections.defaultdict(lambda: [0] * 5)
    n_ativ = 0
    for dim, ids, nomes, insts in zip(a['dimensao'], a['ids_participantes'],
                                      a['nomes_participantes'], a['institutos_participantes']):
        I = [x.strip() for x in ids.split(';') if x.strip()]
        N = [x.strip() for x in str(nomes).split(';')] if isinstance(nomes, str) else []
        T = [x.strip() for x in insts.split(';') if x.strip()]
        assert len(I) == len(T), 'instituto desalinhado'
        for i, t in zip(I, T):
            inst[i] = t
        for i, n in zip(I, N[:len(I)] if len(N) >= len(I) else [None] * len(I)):
            if n and i not in nome:
                nome[i] = n
        S = sorted(set(I))
        if len(S) < 2:
            continue
        n_ativ += 1
        k = DIM.index(dim)
        for u, v in itertools.combinations(S, 2):
            cont[(u, v)][k] += 1

    rows_e = []
    for i in sorted(inst):
        c = cad_d.get(i)
        rows_e.append({'pesquisador_id': i,
                       'nome do pesquisador': c['nome do pesquisador'] if c is not None else nome.get(i, ''),
                       'instituto': inst[i],
                       'area de trabalho': c['area de trabalho'] if c is not None else ''})
    entrada = pd.DataFrame(rows_e)
    rows_s = []
    E = entrada.set_index('pesquisador_id')
    def meta(i):
        r = E.loc[i]
        return r['nome do pesquisador'], r['instituto'], r['area de trabalho']
    for (u, v), c in sorted(cont.items()):
        vec = json.dumps(c)
        nu, iu, au = meta(u); nv, iv, av = meta(v)
        rows_s.append({'nome do pesquisador 1': nu, 'nome do pesquisador 2': nv,
                       'instituto pesquisador 1': iu, 'instituto pesquisador 2': iv,
                       'area de trabalho pesquisador 1': au, 'area de trabalho pesquisador 2': av,
                       'id pesquisador 1': u, 'id pesquisador 2': v, 'vetor contagem': vec})
        rows_s.append({'nome do pesquisador 1': nv, 'nome do pesquisador 2': nu,
                       'instituto pesquisador 1': iv, 'instituto pesquisador 2': iu,
                       'area de trabalho pesquisador 1': av, 'area de trabalho pesquisador 2': au,
                       'id pesquisador 1': v, 'id pesquisador 2': u, 'vetor contagem': vec})
    saida = pd.DataFrame(rows_s)
    leia = pd.DataFrame({'LEIAME': [
        'Base v4: reconstruída do arquivo dataset_atividades_IMC.csv (zip 012783cd, 57.609 linhas, íntegro).',
        f'Atividades com 2+ participantes usadas: {n_ativ}. Pares com laço: {len(cont)}.',
        'Pesos: ART 4 | PRJ 2 | ORI 2 | PTT 1,5 | BAN 0,5 (equação do grupo).',
        'Vetor contagem na ordem [ART, PRJ, ORI, BAN, PTT].',
        'A aba saida (22/11) NÃO foi usada como fonte: não reproduz as atividades deste zip.',
    ]})
    try:
        import xlsxwriter  # noqa: F401
        engine = 'xlsxwriter'
    except ImportError:
        engine = 'openpyxl'   # alternativa instalada junto com o pandas/openpyxl
    with pd.ExcelWriter(os.path.join(PASTA, arquivo_saida), engine=engine) as w:
        leia.to_excel(w, sheet_name='LEIAME', index=False)
        entrada.to_excel(w, sheet_name='entrada', index=False)
        saida.to_excel(w, sheet_name='saida', index=False)
    print('nós:', len(entrada), '| pares:', len(cont), '| linhas saida:', len(saida), '| atividades:', n_ativ)
    print('institutos:', entrada.instituto.value_counts().to_dict())


if __name__ == '__main__':
    for _ini, _fim, _saida in BASES:
        construir(_ini, _fim, _saida)
