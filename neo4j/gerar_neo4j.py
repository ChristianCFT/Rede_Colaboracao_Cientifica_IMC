"""
gerar_neo4j.py — Transforma o Dataset_Entrada_IMC.csv e o Dataset_Saida_IMC.csv
em arquivos prontos para importar no Neo4j (Aura ou Desktop).

O GRAFO HETEROGÊNEO (vários tipos de nó):
  (:Pesquisador)-[:PARTICIPOU {papel}]->(:Atividade {tipo, subtipo, ano, titulo})
  (:Pesquisador)-[:LOTADO_EM]->(:Instituto)
  (:Pesquisador)-[:ATUA_EM]->(:Area)
E AS CAMADAS (derivadas do dataset de saída):
  (:Pesquisador)-[:COLABORA {artigos, projetos, orientacoes, bancas, tecnica, apta}]-(:Pesquisador)

COMO RODAR:
  python gerar_neo4j.py Dataset_Entrada_IMC.csv Dataset_Saida_IMC.csv
  -> cria a pasta neo4j/ com 6 CSVs

Depois siga o passo a passo do importar.cypher.
"""

import csv
import json
import sys
from pathlib import Path

SAIDA = Path("neo4j")
SAIDA.mkdir(exist_ok=True)

# nome da coluna no dataset de entrada -> tipo da atividade no grafo
TIPOS = {
    "artigos_cientificos": "ARTIGO",
    "projetos_pesquisa": "PROJETO",
    "orientacoes": "ORIENTACAO",
    "bancas_academicas": "BANCA",
    "producao_tecnico_tecnologica": "TECNICA",
}


def abrir_csv_escrita(nome, cabecalho):
    f = open(SAIDA / nome, "w", newline="", encoding="utf-8")
    w = csv.writer(f)
    w.writerow(cabecalho)
    return f, w


def main(arq_entrada, arq_saida):
    # utf-8-sig: os arquivos têm BOM (marca invisível no início), isso remove ela
    entrada = open(arq_entrada, encoding="utf-8-sig")
    leitor = csv.DictReader(entrada)

    f_pes, w_pes = abrir_csv_escrita("pesquisadores.csv",
        ["id", "nome", "instituto", "vinculo", "foco_imc", "status", "url_lattes"])
    f_area, w_area = abrir_csv_escrita("pesquisador_area.csv", ["pesquisador_id", "area"])
    f_atv, w_atv = abrir_csv_escrita("atividades.csv", ["id", "tipo", "subtipo", "ano", "titulo"])
    f_par, w_par = abrir_csv_escrita("participacoes.csv", ["pesquisador_id", "atividade_id", "papel"])

    atividades_gravadas = set()       # a mesma atividade aparece no currículo de vários
    participacoes_gravadas = set()    # pesquisadores: grava cada uma só uma vez
    n_pes = 0

    for linha in leitor:
        pid = linha["pesquisador_id"]
        w_pes.writerow([pid, linha["nome_pesquisador"], linha["instituto"], linha["vinculo_unifei"],
                        linha["foco_imc"], linha["status_identificacao"], linha["url_lattes"]])
        n_pes += 1

        for area in linha["area_trabalho"].split("|"):
            area = area.strip()
            if area != "":
                w_area.writerow([pid, area])

        for coluna, tipo in TIPOS.items():
            lista = json.loads(linha[coluna] or "[]")
            for a in lista:
                aid = a["atividade_id"]
                if aid not in atividades_gravadas:
                    atividades_gravadas.add(aid)
                    w_atv.writerow([aid, tipo, a.get("subtipo", ""), a.get("ano", ""),
                                    (a.get("titulo") or "")[:300]])
                for participante in a["participantes_ids"]:
                    papeis = a.get("papeis", {}).get(participante, [""])
                    for papel in papeis:
                        chave = (participante, aid, papel)
                        if chave not in participacoes_gravadas:
                            participacoes_gravadas.add(chave)
                            w_par.writerow([participante, aid, papel])
    entrada.close()
    for f in (f_pes, f_area, f_atv, f_par):
        f.close()

    # ---- camadas: uma relação COLABORA por par, com a contagem de cada tipo
    f_col, w_col = abrir_csv_escrita("colaboracoes.csv",
        ["p1", "p2", "artigos", "projetos", "orientacoes", "bancas", "tecnica", "apta"])
    saida = open(arq_saida, encoding="utf-8-sig")
    n_col = 0
    for linha in csv.DictReader(saida):
        v = json.loads(linha["vetor_bruto"])     # [artigos, projetos, orientações, bancas, técnica]
        w_col.writerow([linha["pesquisador_1_id"], linha["pesquisador_2_id"],
                        v[0], v[1], v[2], v[3], v[4], linha["apta_analise_principal"]])
        n_col += 1
    saida.close()
    f_col.close()

    print(f"Pesquisadores: {n_pes}")
    print(f"Atividades: {len(atividades_gravadas)}")
    print(f"Participações: {len(participacoes_gravadas)}")
    print(f"Pares que colaboram: {n_col}")
    print(f"Arquivos em {SAIDA.resolve()}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("Uso: python gerar_neo4j.py Dataset_Entrada_IMC.csv Dataset_Saida_IMC.csv")
    main(sys.argv[1], sys.argv[2])
