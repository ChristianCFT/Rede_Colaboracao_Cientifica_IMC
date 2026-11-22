"""Peso normalizado da colaboração entre dois pesquisadores (proposta metodológica, seções 4 e 5).

Para cada dimensão k (artigos, projetos, orientações, bancas, produção técnica):
    z_k = ln(1 + x_k) / ln(1 + maior x_k da rede)
O peso da relação é W = soma de α_k · z_k, sempre entre 0 e 1 (α em config.ALFAS).
Os maiores valores são calculados uma única vez sobre todas as relações da rede principal (base comum),
para que o peso de uma relação seja comparável com o de qualquer outra.
"""
import math

from src.config import ALFAS, DIMS


def referencias(arestas: dict) -> list[int]:
    """Maior contagem de cada dimensão entre todas as relações (ordem de DIMS)."""
    maiores = [0] * len(DIMS)
    for e in arestas.values():
        for j, x in enumerate(e['vc']):
            maiores[j] = max(maiores[j], x)
    return maiores


def normalizar(x: int, maior: int) -> float:
    """ln(1 + x) / ln(1 + maior), entre 0 e 1. Dimensão sem nenhuma atividade na rede (maior 0) vale 0."""
    if maior == 0:
        return 0.0
    return math.log1p(x) / math.log1p(maior)


def peso_da_relacao(contagem: list[int], maiores: list[int]) -> float:
    """Soma ponderada das dimensões normalizadas: 0 = nada em comum, 1 = o maior valor da rede em tudo."""
    total = 0.0
    for dim, x, maior in zip(DIMS, contagem, maiores):
        total += ALFAS[dim] * normalizar(x, maior)
    return total


def alfas_em_ordem() -> list[float]:
    """Os α na ordem de DIMS (a mesma do vetor contagem), para o frontend."""
    return [ALFAS[dim] for dim in DIMS]
