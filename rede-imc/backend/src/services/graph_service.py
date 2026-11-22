from src.engine.engine import get_engine
from src.schemas.graph_schema import Graph, NodeDetail


def get_graph() -> Graph:
    return get_engine().graph()


def get_node_detail(node_id: str) -> NodeDetail:
    return get_engine().detail(node_id)
