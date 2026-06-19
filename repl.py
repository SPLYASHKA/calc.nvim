from core.state import State, rollback
from core.engine import execute_command, Command
from core.ops import OPERATIONS
from core.render import RenderStore

OP_ALIASES = {
    "+": "add",
    "*": "mul",
    "-": "sub",
    "!": "store",
    "@": "subst",
}


def parse(line: str) -> Command:
    line = line.strip()

    if not line:
        raise ValueError("empty input")

    if line == "undo":
        return Command(op="__undo__", args={})

    if line in OP_ALIASES:
        return Command(op=OP_ALIASES[line], args={})

    if line in OPERATIONS:
        return Command(op=line, args={})

    return Command(op="push", args={"value": line})


def print_state(state: State, renderer: RenderStore):
    print("STACK:")

    n = len(state.stack)

    for i, nid in enumerate(state.stack):
        rendered = renderer.get(state, nid)
        lines = rendered.pretty.splitlines()

        idx = n - 1 - i

        # первая строка с индексом
        print(f"[{idx}] {lines[0]}")

        # остальные строки с выравниванием
        pad = " " * (len(f"[{idx}] ") )

        for line in lines[1:]:
            print(f"{pad}{line}")

    print("-" * 40)

    print("ENV:")

    for k, nid in state.env.items():
        rendered = renderer.get(state, nid)
        print(f"{k} -> {rendered.pretty}")

    print("-" * 40)


def repl():
    state = State()
    renderer = RenderStore()

    print("RPN VM REPL (implicit push mode)")
    print("Type 'exit' or 'quit' to stop")
    print("Available ops:", ", ".join(OPERATIONS.keys()))
    print("Runtime: undo")
    print()

    while True:
        try:
            line = input("> ").strip()

            if line in ("exit", "quit"):
                break

            if line == "undo":
                rollback(state)
                print("[UNDO]")
                print_state(state, renderer)
                continue

            cmd = parse(line)
            execute_command(state, cmd)

            print_state(state, renderer)

        except Exception as e:
            match type(e).__name__:
                case "StackUnderflowError":
                    print("[STACK ERROR] not enough operands for operation")
                case _:
                    print(f"ERROR: {type(e).__name__}: {e}")


if __name__ == "__main__":
    repl()
