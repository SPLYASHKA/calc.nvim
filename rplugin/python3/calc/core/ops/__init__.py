from sympy import Expr

try:
    from latex2sympy2 import latex2sympy
    HAS_LATEX2SYMPY = True
except ImportError:
    HAS_LATEX2SYMPY = False

from ..errors import StackUnderflowError, StackOperandError, SympyError
from ..state import State, push_result


class Operation:
    def execute(self, state: State, **args) -> None:
        raise NotImplementedError


def pop_expr(state: State) -> Expr:
    if not state.stack:
        raise StackUnderflowError()
    nid = state.stack.pop()
    return state.exprstore[nid]


OPERATIONS = {}
def register(name: str):
    def wrapper(cls):
        OPERATIONS[name] = cls
        return cls
    return wrapper


from . import stack, env, math
