# divide o IMC em Computação e Matemática
import unicodedata

from src.config import REGRAS_AREA


def _norm(s: str) -> str:
    return unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode().lower()


def classificar(area) -> dict:
    """várias áreas = grupo 'Ambas'"""
    if not isinstance(area, str) or not area.strip():
        return dict(comp=False, mat=False, grupo='Sem área')
    t = _norm(area)
    comp = any(_norm(k) in t for k in REGRAS_AREA['Computação'])
    mat = any(_norm(k) in t for k in REGRAS_AREA['Matemática'])
    grupo = 'Ambas' if comp and mat else 'Computação' if comp else 'Matemática' if mat else 'Outras'
    return dict(comp=comp, mat=mat, grupo=grupo)
