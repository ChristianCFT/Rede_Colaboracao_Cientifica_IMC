from fastapi import APIRouter

from src.controllers import graph_controller
from src.schemas.graph_schema import Graph, NodeDetail

router = APIRouter()


@router.get('/graph', response_model=Graph, tags=['graph'],
            summary='Rede principal e pesquisadores sem colaboração com o IMC (nós, arestas, posições, atividades)')
def grafo() -> Graph:
    return graph_controller.get_graph()


@router.get('/nodes/{node_id}', response_model=NodeDetail, tags=['nodes'],
            summary='Detalhes de um pesquisador, com vizinhos e atividades')
def no(node_id: str) -> NodeDetail:
    return graph_controller.get_node_detail(node_id)
