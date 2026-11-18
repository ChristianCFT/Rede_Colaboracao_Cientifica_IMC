"""Rotas HTTP relacionadas ao grafo."""
from typing import Literal

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse

from src.controllers import graph_controller
from src.schemas.graph_schema import Graph, GraphFilter, NodeDetail

router = APIRouter()


@router.get('/graph', response_model=Graph, tags=['graph'], summary='Grafo completo (nós, arestas, posições, métricas)')
def grafo() -> Graph:
    return graph_controller.get_graph()


@router.get('/graph/filter', response_model=Graph, tags=['graph'], summary='Grafo filtrado por área, peso mínimo, tipo ou centralidade')
def filtrar(f: GraphFilter = Depends(GraphFilter.query)) -> Graph:
    return graph_controller.get_filtered_graph(f)


@router.get('/nodes/{node_id}', response_model=NodeDetail, tags=['nodes'], summary='Detalhes de um pesquisador, com vizinhos e atividades')
def no(node_id: str) -> NodeDetail:
    return graph_controller.get_node_detail(node_id)


@router.get('/export/{fmt}', tags=['export'], summary='Baixa o grafo em .gexf (Gephi) ou .graphml (Cytoscape/yEd)')
def exportar(fmt: Literal['gexf', 'graphml']) -> FileResponse:
    return graph_controller.export_graph(fmt)
