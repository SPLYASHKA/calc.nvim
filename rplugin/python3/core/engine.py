from core.state import State, snapshot_state, rollback
from core.ops import OPERATIONS
from core.render import RenderStore
from core.view import build_view

from dataclasses import dataclass

@dataclass
class Command:
    op: str
    args: dict

def execute_command(state: State, command: Command):
    snapshot_state(state)

    try:
        op = OPERATIONS[command.op]()
        op.execute(state, **command.args)

    except Exception:
        rollback(state)
        raise

from typing import Optional
from core.view import ViewState


@dataclass(frozen=True)
class StepResult:
    view: ViewState
    error: Optional[str] = None

def step(state, cmd, renderer: RenderStore) -> StepResult:
    try:
        # meta: undo
        if cmd.op == "__undo__":
            rollback(state)
            return StepResult(
                view=build_view(state, renderer),
                error=None
            )

        execute_command(state, cmd)

        return StepResult(
            view=build_view(state, renderer),
            error=None
        )

    except Exception as e:
        return StepResult(
            view=build_view(state, renderer),
            error=f"{type(e).__name__}: {e}"
        )
