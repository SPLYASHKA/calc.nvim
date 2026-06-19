from dataclasses import dataclass, field
from sympy import Expr


@dataclass
class State:
    stack: list[int] = field(default_factory=list)
    exprstore: dict[int, Expr] = field(default_factory=dict)
    env: dict[str, int] = field(default_factory=dict)
    next_id: int = 1

    history: list[list[int]] = field(default_factory=list)

def snapshot_state(state: State):
    state.history.append(state.stack.copy())

def rollback(state: State):
    if not state.history:
        return

    prev = state.history.pop()

    state.stack = prev.copy()

def push_result(state, expr):
    nid = state.next_id
    state.next_id += 1

    state.exprstore[nid] = expr
    state.stack.append(nid)

    return nid
