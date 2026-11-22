"""Divide o IMC em Computação e Matemática a partir do campo 'area de trabalho'."""
import unicodedata

from src.config import REGRAS_AREA


def _norm(s: str) -> str:
    """Remove acentos e converte para minúsculas."""
    return unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode().lower()


def classificar(area) -> dict:
    """Retorna flags comp/mat e o grupo. Várias áreas => entra nos dois lados (grupo 'Ambas')."""
    if not isinstance(area, str) or not area.strip():
        return dict(comp=False, mat=False, grupo='Sem área')
    t = _norm(area)
    comp = any(_norm(k) in t for k in REGRAS_AREA['Computação'])
    mat = any(_norm(k) in t for k in REGRAS_AREA['Matemática'])
    grupo = 'Ambas' if comp and mat else 'Computação' if comp else 'Matemática' if mat else 'Outras'
    return dict(comp=comp, mat=mat, grupo=grupo)
