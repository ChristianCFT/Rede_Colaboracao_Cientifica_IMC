"""Serviço de negócio do grafo e ponto único de cache em memória."""
from functools import lru_cache
from pathlib import Path

from src.engine.engine import Engine, get_engine
from src.schemas.graph_schema import Graph, GraphFilter, NodeDetail


@lru_cache(maxsize=1)
def get_cached_engine() -> Engine:
    """Mantém o Engine processado em memória.

    Entrada: nenhum argumento.
    Saída: instância única de Engine.
    """
    return get_engine()


def get_graph(filters: GraphFilter | None = None) -> Graph:
    """Retorna o grafo completo ou aplicado aos filtros informados."""
    return get_cached_engine().graph(filters)


def get_node_detail(node_id: str) -> NodeDetail:
    """Retorna os dados e vizinhos de um pesquisador pelo ID."""
    return get_cached_engine().detail(node_id)


def export_graph(fmt: str) -> Path:
    """Exporta o grafo para GEXF ou GraphML e retorna o caminho do arquivo."""
    return get_cached_engine().export(fmt)
