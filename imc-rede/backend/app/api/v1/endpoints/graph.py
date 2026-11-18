from fastapi import APIRouter, Depends
from app.schemas.graph import Graph, GraphFilter
from app.services.graph_engine.engine import get_engine

router = APIRouter(prefix='/graph', tags=['graph'])

@router.get('', response_model=Graph, summary='Grafo completo (nós, arestas, posições, métricas)')
def grafo() -> Graph:
    return get_engine().graph()

@router.get('/filter', response_model=Graph, summary='Grafo filtrado por área, peso mínimo, tipo ou centralidade')
def filtrar(f: GraphFilter = Depends(GraphFilter.query)) -> Graph:
    return get_engine().graph(f)
