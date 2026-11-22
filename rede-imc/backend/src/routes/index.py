from fastapi import APIRouter

from src.config import API_PREFIX
from src.routes.graph_routes import router as graph_router

api_router = APIRouter(prefix=API_PREFIX)
api_router.include_router(graph_router)
