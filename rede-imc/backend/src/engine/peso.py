# peso da colaboração: z_k = ln(1 + x_k) / ln(1 + maior x_k), W = soma(α_k * z_k)
import math

from src.config import ALFAS, DIMS


def referencias(arestas: dict) -> list[int]:
    maiores = [0] * len(DIMS)
    for e in arestas.values():
        for j, x in enumerate(e['vc']):
            maiores[j] = max(maiores[j], x)
    return maiores


def normalizar(x: int, maior: int) -> float:
    """dimensão sem atividade na rede vale 0"""
    if maior == 0:
        return 0.0
    return math.log1p(x) / math.log1p(maior)


def peso_da_relacao(contagem: list[int], maiores: list[int]) -> float:
    total = 0.0
    for dim, x, maior in zip(DIMS, contagem, maiores):
        total += ALFAS[dim] * normalizar(x, maior)
    return total


def alfas_em_ordem() -> list[float]:
    return [ALFAS[dim] for dim in DIMS]
