#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Menu de navegação do projeto de colaboração do IMC.

Coloque este arquivo na mesma pasta dos scripts e das bases. Os scripts
originais são executados em processos separados e não são modificados.
"""
from pathlib import Path
import subprocess
import sys


PASTA = Path(__file__).resolve().parent
PYTHON = sys.executable
# A base agora vem direto dos CSVs da mineração (montar_base.py).
# O build_base_v4.py continua na pasta, mas não é mais chamado pelo menu.
SCRIPT_BASE = "montar_base.py"


def arquivos_faltantes():
    necessarios = {
        "dataset_atividades_IMC.csv",
        "dataset_completo_UNIFEI.csv",
        "dataset_entrada_IMC.csv",
        "dataset_saida_IMC.csv",
        "dataset_IMC_2016_2026.xlsx",
    }
    return sorted(nome for nome in necessarios if not (PASTA / nome).exists())


def executar(arquivo, *argumentos):
    caminho = PASTA / arquivo
    if not caminho.exists():
        print(f"\nArquivo não encontrado: {arquivo}")
        return
    print(f"\nExecutando {arquivo}...\n" + "-" * 78)
    try:
        subprocess.run([PYTHON, str(caminho), *argumentos], cwd=PASTA, check=True)
    except subprocess.CalledProcessError as erro:
        print(f"\nO programa terminou com erro (código {erro.returncode}).")
    except KeyboardInterrupt:
        print("\nExecução interrompida pelo usuário.")
    input("\nPressione ENTER para voltar ao menu...")


def mostrar_status():
    faltantes = arquivos_faltantes()
    print("\nPASTA DO PROJETO")
    print(PASTA)
    print("\nBases principais:")
    print("  OK" if not faltantes else "  Faltando: " + ", ".join(faltantes))
    print("  dataset_IMC_2016_2026.xlsx: " + ("OK" if (PASTA / "dataset_IMC_2016_2026.xlsx").exists() else "FALTANDO"))


def menu():
    while True:
        print("\n" + "=" * 78)
        print("ANÁLISE DA REDE DE COLABORAÇÃO DO IMC")
        print("=" * 78)
        print("1 - Montar a base 2016-2026 a partir dos CSVs da mineração")
        print("2 - Questão 1: grupos e subgrupos (Louvain, trios e influência)")
        print("3 - Questão 2: elos com outros institutos e simulação de remoção")
        print("4 - Análise das quatro camadas")
        print("5 - Executar todas as análises")
        print("6 - Verificar arquivos da pasta")
        print("0 - Sair")
        escolha = input("\nEscolha uma opção: ").strip()

        if escolha == "1":
            executar(SCRIPT_BASE)
        elif escolha == "2":
            executar("q1_terminal.py")
        elif escolha == "3":
            executar("q2_elos.py")
        elif escolha == "4":
            executar("analise_camadas.py")
        elif escolha == "5":
            executar(SCRIPT_BASE)
            executar("q1_terminal.py")
            executar("q2_elos.py")
            executar("analise_camadas.py")
        elif escolha == "6":
            mostrar_status()
            input("\nPressione ENTER para voltar ao menu...")
        elif escolha == "0":
            print("Encerrado.")
            return
        else:
            print("Opção inválida. Escolha um número do menu.")


if __name__ == "__main__":
    menu()
