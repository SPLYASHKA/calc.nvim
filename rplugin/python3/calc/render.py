from typing import Protocol
from dataclasses import dataclass
from pynvim import Nvim

class RenderContext(Protocol):
    nvim: Nvim
    buf: int
    ns: int
    extmark_to_nid: dict[int, int]

@dataclass
class ExtmarkSpec:
    line: int
    col: int
    opts: dict
    nid: int | None

@dataclass
class Layout:
    lines: list[str]
    extmarks: list[ExtmarkSpec]
    cursor: tuple[int, int] | None

def build_layout(result):
    layout = Layout(lines=[], extmarks=[], cursor=None)
    cursor = 0
    cursor = stack_header(layout, cursor)
    cursor = stack_hybrid(layout, result, cursor)
    cursor = dot(layout, cursor)
    cursor = env_pretty(layout, result, cursor)
    return layout

def apply(ctx: RenderContext, layout: Layout, win):
    ctx.nvim.api.buf_set_lines(ctx.buf, 0, -1, False, layout.lines)
    ctx.nvim.api.buf_clear_namespace(ctx.buf, ctx.ns, 0, -1)
    ctx.extmark_to_nid = {}
    for mark in layout.extmarks:
        mark_id = ctx.nvim.api.buf_set_extmark(
            ctx.buf,
            ctx.ns,
            mark.line,
            mark.col,
            mark.opts
        )
        if mark.nid is not None:
            ctx.extmark_to_nid[mark_id] = mark.nid
    ctx.nvim.api.win_set_cursor(win, layout.cursor)
    ctx.nvim.api.win_set_option(win, "conceallevel", 2)


def _append_lines(layout: Layout, lines, start):
    layout.lines.extend(lines)
    return start + len(lines)

def stack_header(layout: Layout, cursor):
    lines = ["## STACK"]
    return _append_lines(layout, lines, cursor)

def stack_pretty(layout: Layout, result, cursor):
    start_render = cursor
    lines = []
    node_ranges = []
    # TODO

    for node in result.view.stack:
        start = cursor

        node_lines = node.pretty.splitlines()
        lines.extend(node_lines)

        cursor += len(node_lines)
        end = cursor - 1

        node_ranges.append((node.nid, start, end))
    _append_lines(layout, lines, start_render)
    # set extmarks
    for i, (nid, start, end) in enumerate(node_ranges):
        ui_index = len(node_ranges) - i

        hl = "Tag" if i % 2 == 0 else "String"

        layout.extmarks.append(ExtmarkSpec(
            start,
            0,
            {
                "end_row": end,
                "end_col": -1,
                "strict": False,
                "hl_group": hl,
                "virt_text": [[f" [nid: {nid}]", "Comment"], [f"[{ui_index}]", "Number"]],
                "virt_text_pos": "right_align",
            },
            nid
            ))
    return cursor

def stack_hybrid(layout: Layout, result, cursor):
    node_ranges = []

    for node in result.view.stack:
        start = cursor

        layout.lines.append(f"$${node.latex}$$")

        cursor += 1
        end = cursor - 1

        node_ranges.append((node, start, end))

    for i, (node, start, end) in enumerate(node_ranges):
        ui_index = len(node_ranges) - i

        hl = "Tag" if i % 2 == 0 else "String"

        pretty_lines = [
            [(line, "Macro")]
            for line in node.pretty.splitlines()
        ]

        layout.extmarks.append(
            ExtmarkSpec(
                start,
                0,
                {
                    "end_row": end,
                    "end_col": -1,
                    "strict": False,
                    "hl_group": hl,

                    "virt_lines": pretty_lines,
                    # "virt_lines_above": True,

                    "virt_text": [
                        [f" [nid: {node.nid}]", "Comment"],
                        [f"[{ui_index}]", "Number"],
                    ],
                    "virt_text_pos": "right_align",
                     "conceal": "",
                },
                node.nid,
            )
        )

    return cursor

def dot(layout: Layout, cursor):
    dot_cursor = cursor
    lines = []
    lines.append(".")
    lines.append("")
    cursor = _append_lines(layout, lines, cursor)
    # set extmarks
    layout.extmarks.append(ExtmarkSpec(
        dot_cursor,
        0,
        {
            "end_col": 1,
            "hl_group": "TermCursor"
        },
        None
    ))
    layout.cursor = (dot_cursor + 1, 0) # 1-based
    return cursor

def init_calc_buffer(nvim, buf):
    """Fill a fresh calc buffer with initial layout."""
    nvim.api.buf_set_lines(buf, 0, -1, False, [
        "## STACK",
        "type i or :Calc to interact",
        ".",
        "",
        "## ENV",
    ])


def env_pretty(layout: Layout, result, cursor):
    # TODO: ugly, do better
    lines = ["## ENV"]

    for name, node in result.view.env.items():
        lines.append(f"{name} =")
        block = node.pretty.splitlines()
        lines.extend(block)

    if result.error:
        lines.append("")
        lines.append("ERROR:")

        lines.extend(
            str(result.error).splitlines()
        )

    return _append_lines(layout, lines, cursor)


