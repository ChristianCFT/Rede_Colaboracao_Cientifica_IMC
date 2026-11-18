from fastapi import APIRouter
from app.schemas.graph import NodeDetail
from app.services.graph_engine.engine import get_engine

router = APIRouter(prefix='/nodes', tags=['nodes'])

@router.get('/{node_id}', response_model=NodeDetail, summary='Detalhes de um pesquisador, com vizinhos e atividades')
def no(node_id: str) -> NodeDetail:
    return get_engine().detail(node_id)
