from sympy import Expr, sympify, Symbol
from sympy import expand, factor
from .errors import StackUnderflowError, SympyError, StackOperandError

try:
    from latex2sympy2 import latex2sympy
    HAS_LATEX2SYMPY = True
except ImportError:
    HAS_LATEX2SYMPY = False
from .state import State, push_result

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

class BinaryOperation(Operation):
    def apply(self, a: Expr, b: Expr) -> Expr:
        raise NotImplementedError

    def execute(self, state: State, **args):
        b = pop_expr(state)
        a = pop_expr(state)

        try:
            result = self.apply(a, b)
        except Exception:
            raise SympyError

        push_result(state, result)

@register("add")
class AddOperation(BinaryOperation):
    def apply(self, a, b):
        return a + b

@register("mul")
class MulOperation(BinaryOperation):
    def apply(self, a, b):
        return a * b

@register("div")
class DivOperation(BinaryOperation):
    def apply(self, a, b):
        return a / b

@register("sub")
class SubOperation(BinaryOperation):
    def apply(self, a, b):
        return a - b

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
                    expr = sympify(raw)

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

@register("store")
class StoreOperation(Operation):
    def execute(self, state: State, **args):
        if len(state.stack) < 2:
            raise StackUnderflowError("store: needs 2 operands")

        key_expr = pop_expr(state)
        value_nid = state.stack.pop()

        if not isinstance(key_expr, Symbol):
            raise StackOperandError("store: key must be Symbol")

        key = str(key_expr)

        state.env[key] = value_nid

@register("subst")
class SubstOperation(Operation):
    def execute(self, state: State, **args):
        if len(state.stack) < 2:
            raise StackUnderflowError("sub: needs 2 operands")

        symbol_nid = state.stack.pop()
        expr_nid = state.stack.pop()

        expr = state.exprstore[expr_nid]
        symbol_expr = state.exprstore[symbol_nid]

        if not isinstance(symbol_expr, Symbol):
            raise StackOperandError("sub: top operand must be Symbol")

        name = str(symbol_expr)

        if name not in state.env:
            raise StackOperandError(f"sub: {name} not in env")

        replacement_nid = state.env[name]
        replacement_expr = state.exprstore[replacement_nid]

        result = expr.subs({symbol_expr: replacement_expr})

        push_result(state, result)

@register("eval")
class EvalOperation(Operation):
    def execute(self, state: State, **args):
        expr = pop_expr(state)

        subs_map = {
            Symbol(k): state.exprstore[nid]
            for k, nid in state.env.items()
        }

        result = expr.subs(subs_map)

        push_result(state, result)

@register("diff")
class DiffOperation(Operation):
    def execute(self, state: State, **args):
        expr = pop_expr(state)

        raw_args = args.get("wrt", []) # with respect to

        diff_args = []

        for item in raw_args:
            if item.isdigit():
                diff_args.append(int(item))
            else:
                diff_args.append(Symbol(item))

        try:
            result = expr.diff(*diff_args)
        except Exception as e:
            raise SympyError(str(e))

        push_result(state, result)

@register("det")
class DetOperation(Operation):
    def execute(self, state: State, **args):
        expr = pop_expr(state)

        try:
            result = expr.det()
        except Exception as e:
            raise SympyError(
                str(e) or type(e).__name__
            )
        push_result(state, result)

@register("expand")
class ExpandOperation(Operation):
    def execute(self, state, **args):
        expr = pop_expr(state)
        try:
            result = expand(expr)
        except Exception as e:
            raise SympyError(str(e))
        push_result(state, result)

@register("factor")
class FactorOperation(Operation):
    def execute(self, state, **args):
        expr = pop_expr(state)
        try:
            result = factor(expr)
        except Exception as e:
            raise SympyError(str(e))
        push_result(state, result)
