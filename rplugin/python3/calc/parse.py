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
