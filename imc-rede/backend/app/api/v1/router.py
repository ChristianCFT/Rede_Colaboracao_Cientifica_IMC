from fastapi import APIRouter
from app.api.v1.endpoints import export, graph, nodes

api_router = APIRouter()
for m in (graph, nodes, export):
    api_router.include_router(m.router)
