"""Modelos Pydantic da API: nós, arestas, métricas, áreas e filtros."""
from typing import Literal
from fastapi import Query
from pydantic import BaseModel, Field

Grupo = Literal['Computação', 'Matemática', 'Ambas', 'Outras', 'Sem área', '']

class Producao(BaseModel):
    art: int; prj: int; ori: int; ban: int; ptt: int

class Node(BaseModel):
    id: str
    label: str
    instituto: str
    area: str
    grupo: Grupo
    comp: bool
    mat: bool
    grau: int
    centralidade_grau: float
    intermediacao: float
    lattes_url: str
    observacao: str
    producao: Producao | None
    x: float; y: float            # layout livre
    x_area: float; y_area: float  # layout separado por área

class Edge(BaseModel):
    source: str
    target: str
    tipo_relacao: str
    escopo: str
    area_imc: str
    vetor_contagem: list[int] = Field(min_length=5, max_length=5)
    vetor_bruto: list[list[str]]
    soma_bruta: int

class Atividade(BaseModel):
    ano: str
    titulo: str

class NetworkMetrics(BaseModel):
    nos: int
    arestas: int
    densidade: float
    grau_medio: float
    componentes: int

class Area(BaseModel):
    nome: str
    cor: str
    total: int

class Graph(BaseModel):
    nodes: list[Node]
    edges: list[Edge]
    atividades: dict[str, Atividade]
    areas: list[Area]
    paleta: dict[str, str]
    cores_grupo: dict[str, str]
    dimensoes: list[str]
    metricas: NetworkMetrics

class GraphFilter(BaseModel):
    """Filtros do endpoint /graph/filter (query string)."""
    grupos: list[str] | None = None
    tipos: list[str] | None = None
    peso_min: int = 1
    centralidade_min: float = 0.0
    incluir_externos: bool = True

    @classmethod
    def query(cls, grupos: list[str] | None = Query(None, description='Computação, Matemática, Outras'),
              tipos: list[str] | None = Query(None, description='ex.: IMC-IMC, IMC-EXT'),
              peso_min: int = Query(1, ge=1), centralidade_min: float = Query(0.0, ge=0, le=1),
              incluir_externos: bool = True) -> 'GraphFilter':
        return cls(grupos=grupos, tipos=tipos, peso_min=peso_min, centralidade_min=centralidade_min,
                   incluir_externos=incluir_externos)

class AtividadeDetalhe(Atividade):
    id: str
    dimensao: str

class Vizinho(BaseModel):
    id: str
    label: str
    instituto: str
    tipo_relacao: str
    soma_bruta: int
    vetor_contagem: list[int]
    atividades: list[AtividadeDetalhe]

class NodeDetail(Node):
    vizinhos: list[Vizinho]
