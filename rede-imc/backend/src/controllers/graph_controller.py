from fastapi import HTTPException

from src.engine.engine import NodeNotFound
from src.schemas.graph_schema import Graph, NodeDetail
from src.services import graph_service


def get_graph() -> Graph:
    return graph_service.get_graph()


def get_node_detail(node_id: str) -> NodeDetail:
    try:
        return graph_service.get_node_detail(node_id)
    except NodeNotFound as exc:
        raise HTTPException(status_code=404, detail=f'Pesquisador {exc} não encontrado') from exc
