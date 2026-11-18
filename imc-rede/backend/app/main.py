"""FastAPI: uvicorn app.main:app --reload --port 8000  (docs em /docs)"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api.v1.router import api_router
from app.core.config import API_PREFIX, CORS_ORIGINS
from app.services.graph_engine.engine import NodeNotFound, get_engine

log = logging.getLogger('imc-rede')

@asynccontextmanager
async def lifespan(_: FastAPI):
    get_engine()  # aquece o cache no start-up
    yield

app = FastAPI(title='IMC Rede API', version='1.0.0', lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=CORS_ORIGINS, allow_methods=['GET'], allow_headers=['*'])
app.include_router(api_router, prefix=API_PREFIX)

@app.exception_handler(NodeNotFound)
async def _nf(_: Request, e: NodeNotFound) -> JSONResponse:
    return JSONResponse(status_code=404, content={'detail': f'Pesquisador {e} não encontrado'})

@app.exception_handler(Exception)
async def _err(_: Request, e: Exception) -> JSONResponse:
    log.exception('erro não tratado')
    return JSONResponse(status_code=500, content={'detail': 'Erro interno do servidor'})

@app.get('/health', tags=['meta'])
def health() -> dict[str, str]:
    return {'status': 'ok'}
