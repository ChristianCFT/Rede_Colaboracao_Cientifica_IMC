"""Adaptador HTTP: recebe dados da rota e converte erros de domínio em respostas HTTP."""
import logging
from typing import Literal

from fastapi import HTTPException
from fastapi.responses import FileResponse

from src.engine.engine import NodeNotFound
from src.schemas.graph_schema import Graph, GraphFilter, NodeDetail
from src.services import graph_service

log = logging.getLogger('imc-rede')


def get_graph() -> Graph:
    """Obtém o grafo completo via serviço."""
    try:
        return graph_service.get_graph()
    except Exception as exc:
        log.exception('erro ao obter grafo')
        raise HTTPException(status_code=500, detail='Erro interno do servidor') from exc


def get_filtered_graph(filters: GraphFilter) -> Graph:
    """Obtém o grafo filtrado via serviço."""
    try:
        return graph_service.get_graph(filters)
    except Exception as exc:
        log.exception('erro ao filtrar grafo')
        raise HTTPException(status_code=500, detail='Erro interno do servidor') from exc


def get_node_detail(node_id: str) -> NodeDetail:
    """Obtém os detalhes de um nó ou converte nó ausente em 404."""
    try:
        return graph_service.get_node_detail(node_id)
    except NodeNotFound as exc:
        raise HTTPException(status_code=404, detail=f'Pesquisador {exc} não encontrado') from exc
    except Exception as exc:
        log.exception('erro ao obter detalhe do nó')
        raise HTTPException(status_code=500, detail='Erro interno do servidor') from exc


def export_graph(fmt: Literal['gexf', 'graphml']) -> FileResponse:
    """Gera ou reutiliza um arquivo de exportação e o devolve ao cliente."""
    try:
        path = graph_service.export_graph(fmt)
        return FileResponse(path, filename=f'grafo_IMC.{fmt}', media_type='application/xml')
    except Exception as exc:
        log.exception('erro ao exportar grafo')
        raise HTTPException(status_code=500, detail='Erro interno do servidor') from exc
