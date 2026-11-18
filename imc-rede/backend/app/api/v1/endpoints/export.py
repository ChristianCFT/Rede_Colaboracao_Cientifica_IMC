from typing import Literal
from fastapi import APIRouter
from fastapi.responses import FileResponse
from app.services.graph_engine.engine import get_engine

router = APIRouter(prefix='/export', tags=['export'])

@router.get('/{fmt}', summary='Baixa o grafo em .gexf (Gephi) ou .graphml (Cytoscape/yEd)')
def exportar(fmt: Literal['gexf', 'graphml']) -> FileResponse:
    return FileResponse(get_engine().export(fmt), filename=f'grafo_IMC.{fmt}', media_type='application/xml')
