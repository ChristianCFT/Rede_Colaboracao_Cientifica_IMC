"""
Lê os currículos Lattes e gera os 4 CSVs da rede.

Uso: python main.py [--entrada ZIP_OU_PASTA] [--saida PASTA]
"""
import argparse
from pathlib import Path

from configuracao import ENTRADA_PADRAO, SAIDA_PADRAO
from src import csvs, curriculos, deduplicacao, externos, identificacao, professores, rede


def main():
    leitor = argparse.ArgumentParser(description='Gera os 4 CSVs da rede de colaboração da UNIFEI.')
    leitor.add_argument('--entrada', default=ENTRADA_PADRAO,
                        help='ZIP com os currículos ou a pasta já extraída')
    leitor.add_argument('--saida', default=SAIDA_PADRAO, help='pasta onde os 4 CSVs são gravados')
    argumentos = leitor.parse_args()

    print('[1/6] Lendo índices, pastas e cabeçalhos dos currículos...')
    raiz = professores.abrir_entrada(Path(argumentos.entrada))
    lista_professores = professores.carregar_professores(raiz)

    print('[2/6] Extraindo as cinco dimensões de cada currículo...')
    indice = identificacao.montar_indice(lista_professores, identificacao.ler_correspondencias())
    itens = curriculos.extrair_itens(lista_professores, indice)

    print('[3/6] Conferindo externos que podem ser professores ou que têm dois ids...')
    externos.corrigir_externos(itens, lista_professores, indice)
    juntados, avisos = externos.unificar_externos_por_nome(itens, indice)
    print(f'   {juntados} externos citados só pelo nome passaram a usar o id do Lattes')
    for aviso in avisos:
        print(f'   aviso: {aviso}')
    juntados, avisos = externos.unificar_nomes_do_meio(itens, indice)
    print(f'   {juntados} externos com o nome do meio faltando foram juntados ao nome completo')
    for aviso in avisos:
        print(f'   aviso: {aviso}')

    print('[4/6] Juntando registros repetidos em atividades únicas...')
    atividades = deduplicacao.deduplicar(itens)

    print('[5/6] Montando os pares e os vetores da camada...')
    rede_da_camada = rede.montar_rede(atividades, lista_professores)

    print('[6/6] Gravando os 4 CSVs...')
    csvs.gravar_csvs(Path(argumentos.saida), lista_professores, indice['externos'], rede_da_camada)
    print(f'Pronto: {len(itens)} registros, {len(atividades)} atividades únicas, '
          f"{len(rede_da_camada['pares'])} relações. CSVs em {argumentos.saida}")


if __name__ == '__main__':
    main()
