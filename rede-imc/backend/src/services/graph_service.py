"""Camada de serviço do grafo. O Engine (e seu cache em memória) vive em src.engine.engine.get_engine."""
from src.engine.engine import get_engine
from src.schemas.graph_schema import Graph, NodeDetail


def get_graph() -> Graph:
    """Retorna a rede principal e os pesquisadores sem colaboração com o IMC."""
    return get_engine().graph()


def get_node_detail(node_id: str) -> NodeDetail:
    """Retorna os dados e vizinhos de um pesquisador pelo ID."""
    return get_engine().detail(node_id)
