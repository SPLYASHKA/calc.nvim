from sympy import Symbol

from ..errors import StackUnderflowError, StackOperandError
from ..state import State, push_result
from . import Operation, register, pop_expr


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
