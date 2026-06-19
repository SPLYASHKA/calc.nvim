from dataclasses import dataclass

@dataclass(frozen=True)
class Rendered:
    text: str
    pretty: str
    latex: str

from sympy import pretty, latex

def render_expr(expr) -> Rendered:
    return Rendered(
        text=str(expr),
        pretty=pretty(expr),
        latex=latex(expr),
    )

class RenderStore:
    def __init__(self):
        self._cache: dict[int, Rendered] = {}

    def get(self, state, nid: int) -> Rendered:
        if nid not in self._cache:
            expr = state.exprstore[nid]
            self._cache[nid] = render_expr(expr)

        return self._cache[nid]
