from core.state import State, snapshot_state, rollback
from core.ops import OPERATIONS

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
