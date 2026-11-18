"""Adaptador HTTP: converte erros de domínio em respostas HTTP.

Erros inesperados não são tratados aqui: o handler global de src/main.py registra o log e devolve 500.
"""
from fastapi import HTTPException

from src.engine.engine import NodeNotFound
from src.schemas.graph_schema import Graph, NodeDetail
from src.services import graph_service


def get_graph() -> Graph:
    """Obtém o grafo via serviço."""
    return graph_service.get_graph()


def get_node_detail(node_id: str) -> NodeDetail:
    """Obtém os detalhes de um nó ou converte nó ausente em 404."""
    try:
        return graph_service.get_node_detail(node_id)
    except NodeNotFound as exc:
        raise HTTPException(status_code=404, detail=f'Pesquisador {exc} não encontrado') from exc
