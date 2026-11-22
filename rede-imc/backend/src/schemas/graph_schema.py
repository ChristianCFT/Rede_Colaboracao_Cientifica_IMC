from typing import Literal

from pydantic import BaseModel, Field

Grupo = Literal['Computação', 'Matemática', 'Ambas', 'Outras', 'Sem área', '']


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
    peso: float           # 0 a 1


class PesoParametros(BaseModel):
    alfas: list[float]        # peso de cada dimensão
    referencias: list[int]    # maior contagem de cada dimensão


class Atividade(BaseModel):
    ano: str
    titulo: str


class Graph(BaseModel):
    nodes: list[Node]                 # rede principal
    edges: list[Edge]
    sem_colaboracao: list[Node]       # só vértices
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
