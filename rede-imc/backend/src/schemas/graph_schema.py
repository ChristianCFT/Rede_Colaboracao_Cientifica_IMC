"""Modelos Pydantic da API: nós, arestas, atividades e detalhes de um pesquisador."""
from typing import Literal

from pydantic import BaseModel, Field

Grupo = Literal['Computação', 'Matemática', 'Ambas', 'Outras', 'Sem área', '']


class Producao(BaseModel):
    art: int
    prj: int
    ori: int
    ban: int
    ptt: int


class Node(BaseModel):
    id: str
    label: str
    instituto: str
    area: str
    grupo: Grupo
    comp: bool
    mat: bool
    grau: int
    lattes_url: str
    observacao: str
    producao: Producao | None
    x: float              # layout livre
    y: float
    x_area: float         # layout separado por área
    y_area: float


class Edge(BaseModel):
    source: str
    target: str
    tipo_relacao: str
    vetor_contagem: list[int] = Field(min_length=5, max_length=5)
    vetor_bruto: list[list[str]]
    soma_bruta: int
    peso: float           # peso normalizado da colaboração, de 0 a 1 (engine/peso.py)


class PesoParametros(BaseModel):
    """O que o frontend precisa para recalcular o peso no recorte (filtros de dimensão e período)."""
    alfas: list[float]        # importância de cada dimensão, na ordem do vetor contagem (soma 1)
    referencias: list[int]    # maior contagem de cada dimensão na rede inteira (base comum)


class Atividade(BaseModel):
    ano: str
    titulo: str


class Graph(BaseModel):
    nodes: list[Node]                 # rede principal de colaboração do IMC
    edges: list[Edge]
    sem_colaboracao: list[Node]       # pesquisadores sem colaboração direta com o IMC (só vértices, sem relações)
    atividades: dict[str, Atividade]
    paleta: dict[str, str]
    cores_grupo: dict[str, str]
    dimensoes: list[str]
    peso: PesoParametros


class AtividadeDetalhe(Atividade):
    id: str
    dimensao: str


class Vizinho(BaseModel):
    id: str
    label: str
    instituto: str
    tipo_relacao: str
    soma_bruta: int
    peso: float
    vetor_contagem: list[int]
    atividades: list[AtividadeDetalhe]


class NodeDetail(Node):
    vizinhos: list[Vizinho]
