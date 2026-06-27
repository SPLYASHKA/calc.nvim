from sympy import sympify
from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication

from ..errors import StackUnderflowError, SympyError
from ..state import State, push_result
from . import Operation, register, pop_expr, HAS_LATEX2SYMPY

if HAS_LATEX2SYMPY:
    from latex2sympy2 import latex2sympy


_SYMPY_TRANSFORMATIONS = standard_transformations + (implicit_multiplication,)


@register("drop")
class DropOperation(Operation):
    def execute(self, state: State, **args):
        if not state.stack:
            raise StackUnderflowError("drop: empty stack")
        state.stack.pop()


@register("push")
class PushOperation(Operation):
    def execute(self, state, **args):
        raw = args.get("value")
        fmt = args.get("format", "sympy")

        if raw is None:
            raise ValueError("push requires 'value'")

        try:
            match fmt:
                case "sympy":
                    expr = parse_expr(raw, transformations=_SYMPY_TRANSFORMATIONS)

                case "latex":
                    if not HAS_LATEX2SYMPY:
                        raise SympyError("latex2sympy2 not installed. Run: pip install latex2sympy2")
                    expr = sympify(str(latex2sympy(raw)))

                case _:
                    raise ValueError(f"unknown format: {fmt}")

        except SympyError:
            raise
        except Exception as e:
            raise SympyError(f"Invalid push input: {raw}") from e

        push_result(state, expr)


@register("dup")
class DupOperation(Operation):
    def execute(self, state, **args):
        if not state.stack:
            raise StackUnderflowError()
        nid = state.stack[-1]
        state.stack.append(nid)


@register("pick")
class PickOperation(Operation):
    def execute(self, state, **args):
        k = args.get("index")
        if k is None:
            raise ValueError("pick requires 'index'")
        k = int(k)
        if k < 0 or k >= len(state.stack):
            raise StackUnderflowError()
        nid = state.stack[-1 - k]
        state.stack.append(nid)


@register("swap")
class SwapOperation(Operation):
    def execute(self, state, **args):
        if len(state.stack) < 2:
            raise StackUnderflowError(f"swap requires 2 operands, got {len(state.stack)}")
        a = state.stack[-2]
        b = state.stack[-1]
        state.stack[-2] = b
        state.stack[-1] = a
