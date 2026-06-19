from core import State, Command, step, RenderStore
from core.ops import OPERATIONS


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


def print_state(view_state):
    print("STACK:")

    n = len(view_state.stack)

    for i, node in enumerate(view_state.stack):
        lines = node.pretty.splitlines()

        idx = n - 1 - i

        print(f"[{idx}] {lines[0]}")

        pad = " " * (len(f"[{idx}] ") )

        for line in lines[1:]:
            print(f"{pad}{line}")

    print("-" * 40)

    print("ENV:")

    for k, node in view_state.env.items():
        print(f"{k} -> {node.pretty}")

    print("-" * 40)


def repl():
    state = State()
    renderer = RenderStore()

    print("RPN SYSTEM REPL (step API)")
    print("Type 'exit' or 'quit' to stop")
    print("Available ops:", ", ".join(OPERATIONS.keys()))
    print("Runtime: undo")
    print()

    while True:
        try:
            line = input("> ").strip()

            if line in ("exit", "quit"):
                break

            cmd = parse(line)

            result = step(state, cmd, renderer)

            print_state(result.view)

            if result.error:
                print(f"[ERROR] {result.error}")

        except Exception as e:
            print(f"FATAL ERROR: {type(e).__name__}: {e}")


if __name__ == "__main__":
    repl()
