from calc.core import Command
from calc.core.ops import OPERATIONS

OP_ALIASES = {
    "+": "add",
    "*": "mul",
    "-": "sub",
    "/": "div",
    "!": "store",
    "@": "subst",
}

PARSERS = {}
def parse_command(name: str):
    def deco(fn):
        PARSERS[name] = fn
        return fn
    return deco

@parse_command("diff")
def parse_diff(tail: list[str]) -> dict:
    return {"wrt": tail}

@parse_command("pick")
def parse_pick(tail: list[str]) -> dict:
    if not tail:
        return {}
    # user-facing 1-based → core 0-based
    return {"index": str(int(tail[0]) - 1)}

def parse(token: str) -> Command:
    token = token.strip()
    parts = token.split()

    if not parts:
        raise ValueError("empty command")

    head, tail = parts[0], parts[1:]

    # meta ops
    if head == "undo":
        return Command(op="__undo__", args={})

    if head in OP_ALIASES:
        return Command(op=OP_ALIASES[head], args={})

    if head in OPERATIONS:
        parser = PARSERS.get(head)
        args = parser(tail) if parser else {}
        return Command(op=head, args=args)

    # push if head is not OP
    return Command(op="push", args={"value": token})
