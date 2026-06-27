from sympy import Expr, Symbol, expand, factor

from ..errors import SympyError
from ..state import State, push_result
from . import Operation, register, pop_expr


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


@register("diff")
class DiffOperation(Operation):
    def execute(self, state: State, **args):
        expr = pop_expr(state)

        raw_args = args.get("wrt", [])

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
            raise SympyError(str(e) or type(e).__name__)

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
