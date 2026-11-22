"""
Recorte temporal dos 4 CSVs da rede de colaboração do IMC/UNIFEI.

Lê os 4 CSVs da pasta dados/, mantém só as atividades de ANO_INICIO a ANO_FIM
e grava os 4 CSVs recortados na pasta resultados/, com os mesmos nomes,
as mesmas colunas e o mesmo formato dos originais.

Regra do recorte: vale a coluna 'ano' de cada atividade (nos projetos,
é o ano de início), a mesma regra para as cinco dimensões.

Como rodar:  python main.py
"""

import csv
import json
import re
from pathlib import Path

ANO_INICIO = 2016
ANO_FIM = 2026

PASTA = Path(__file__).parent
DADOS = PASTA / "dados"
RESULTADOS = PASTA / "resultados"

ARQUIVO_COMPLETO = "dataset_completo_UNIFEI.csv"
ARQUIVO_ENTRADA = "dataset_entrada_IMC.csv"
ARQUIVO_SAIDA = "dataset_saida_IMC.csv"
ARQUIVO_ATIVIDADES = "dataset_atividades_IMC.csv"

# Colunas de listas da entrada, na ordem do vetor [ART, PRJ, ORI, BAN, PTT].
COLUNAS_LISTAS = [
    "artigos científicos",
    "projetos de pesquisa",
    "orientação",
    "bancas acadêmicas",
    "produção técnico-tecnológica",
]

NOTA_SEM_RELACAO = "professor do IMC sem relação identificada"


# ---------------------------------------------------------------- leitura e gravação

def ler_csv(nome):
    """Devolve (colunas, linhas) de um CSV da pasta dados/."""
    with open(DADOS / nome, encoding="utf-8-sig", newline="") as arquivo:
        leitor = csv.DictReader(arquivo)
        return leitor.fieldnames, list(leitor)


def gravar_csv(nome, colunas, linhas):
    """Grava um CSV na pasta resultados/ no mesmo formato dos originais."""
    with open(RESULTADOS / nome, "w", encoding="utf-8-sig", newline="") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=colunas, lineterminator="\r\n")
        escritor.writeheader()
        escritor.writerows(linhas)


def para_texto(valor):
    """Converte uma lista para o texto usado nos CSVs, ex.: ["ART-1", "ART-2"]."""
    return json.dumps(valor, ensure_ascii=False)


# ---------------------------------------------------------------- recortes

def recortar_atividades(atividades):
    """Fica só com as atividades cujo ano está dentro do recorte."""
    return [a for a in atividades if ANO_INICIO <= int(a["ano"]) <= ANO_FIM]


def recortar_saida(saida, ids_validos):
    """Filtra as listas do vetor bruto e apaga as linhas que ficam zeradas."""
    novas_linhas = []
    for linha in saida:
        listas = json.loads(linha["vetor bruto"])
        listas = [[i for i in lista if i in ids_validos] for lista in listas]
        contagem = [len(lista) for lista in listas]

        if sum(contagem) == 0:
            continue

        linha["vetor bruto"] = para_texto(listas)
        linha["vetor contagem"] = para_texto(contagem)
        novas_linhas.append(linha)
    return novas_linhas


def contar_participacoes(atividades):
    """Conta em quantas atividades do recorte cada pesquisador aparece."""
    contagem = {}
    for atividade in atividades:
        ids = {i for i in atividade["ids_participantes"].split(";") if i}
        for pesquisador in ids:
            contagem[pesquisador] = contagem.get(pesquisador, 0) + 1
    return contagem


def ajustar_observacao(texto, qtd_atividades, sem_relacao):
    """Atualiza o número de atividades citado e a nota de 'sem relação'."""
    partes = [p for p in texto.split("; ") if p and p != NOTA_SEM_RELACAO]
    partes = [
        re.sub(r"aparece em \d+ atividade", f"aparece em {qtd_atividades} atividade", p)
        for p in partes
    ]
    if sem_relacao:
        partes.append(NOTA_SEM_RELACAO)
    return "; ".join(partes)


def recortar_entrada(entrada, ids_validos, ids_com_relacao, participacoes):
    """
    Mantém os docentes do IMC e quem ainda aparece na saída (mesma regra
    da base original), filtrando as listas de atividades de cada um.
    """
    novas_linhas = []
    for linha in entrada:
        pesquisador = linha["pesquisador_id"]
        e_do_imc = linha["instituto"] == "IMC"

        if not e_do_imc and pesquisador not in ids_com_relacao:
            continue

        # Externos e quem não tem currículo têm os campos vazios: continuam vazios.
        if linha["vetor contagem"] != "":
            listas = [json.loads(linha[coluna]) for coluna in COLUNAS_LISTAS]
            listas = [[i for i in lista if i in ids_validos] for lista in listas]
            for coluna, lista in zip(COLUNAS_LISTAS, listas):
                linha[coluna] = para_texto(lista)
            linha["vetor contagem"] = para_texto([len(lista) for lista in listas])

        linha["observacao"] = ajustar_observacao(
            linha["observacao"],
            participacoes.get(pesquisador, 0),
            e_do_imc and pesquisador not in ids_com_relacao,
        )
        novas_linhas.append(linha)
    return novas_linhas


# ---------------------------------------------------------------- principal

def main():
    colunas_completo, completo = ler_csv(ARQUIVO_COMPLETO)
    colunas_entrada, entrada = ler_csv(ARQUIVO_ENTRADA)
    colunas_saida, saida = ler_csv(ARQUIVO_SAIDA)
    colunas_atividades, atividades = ler_csv(ARQUIVO_ATIVIDADES)
    antes = [len(completo), len(entrada), len(saida), len(atividades)]

    atividades = recortar_atividades(atividades)
    ids_validos = {a["id_atividade"] for a in atividades}

    saida = recortar_saida(saida, ids_validos)
    ids_com_relacao = {s["id pesquisador 1"] for s in saida} | {s["id pesquisador 2"] for s in saida}

    participacoes = contar_participacoes(atividades)
    entrada = recortar_entrada(entrada, ids_validos, ids_com_relacao, participacoes)

    # O dataset completo é o cadastro dos docentes: não tem ano, sai igual.

    RESULTADOS.mkdir(exist_ok=True)
    gravar_csv(ARQUIVO_COMPLETO, colunas_completo, completo)
    gravar_csv(ARQUIVO_ENTRADA, colunas_entrada, entrada)
    gravar_csv(ARQUIVO_SAIDA, colunas_saida, saida)
    gravar_csv(ARQUIVO_ATIVIDADES, colunas_atividades, atividades)

    depois = [len(completo), len(entrada), len(saida), len(atividades)]
    nomes = [ARQUIVO_COMPLETO, ARQUIVO_ENTRADA, ARQUIVO_SAIDA, ARQUIVO_ATIVIDADES]
    print(f"Recorte {ANO_INICIO}-{ANO_FIM} gravado em {RESULTADOS.name}/")
    for nome, n_antes, n_depois in zip(nomes, antes, depois):
        print(f"  {nome:<30} {n_antes:>6} -> {n_depois:>6} linhas")


if __name__ == "__main__":
    main()
