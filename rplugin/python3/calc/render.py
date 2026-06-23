from typing import Protocol
from pynvim import Nvim

class RenderContext(Protocol):
    nvim: Nvim
    buf: int
    ns: int
    stack_win: object
    extmark_to_nid: dict[int, int]

def render(ctx: RenderContext, result):
    render_pretty(ctx, result)

def render_pretty(ctx: RenderContext, result):
    lines = []
    node_ranges = []

    lines.append("STACK")
    cursor = 1 # 0-based

    for node in result.view.stack:
        start = cursor

        node_lines = node.pretty.splitlines()
        lines.extend(node_lines)

        cursor += len(node_lines)
        end = cursor - 1

        node_ranges.append((node.nid, start, end))

    dot_cursor = cursor

    lines.append(".")
    lines.append("")
    lines.append("ENV")

    for name, node in result.view.env.items():
        lines.append(f"{name} =")
        lines.extend(node.pretty.splitlines())

    if result.error:
        lines.append("")
        lines.append(f"ERROR: {result.error}")

    ctx.nvim.api.buf_set_lines(
        ctx.buf, 0, -1, False, lines
    )

    ctx.nvim.api.win_set_cursor(ctx.stack_win, (dot_cursor + 1, 0)) # 1-based

    # clear extmarks
    ctx.nvim.api.buf_clear_namespace(ctx.buf, ctx.ns, 0, -1)
    ctx.extmark_to_nid = {}

    # set extmarks
    for i, (nid, start, end) in enumerate(node_ranges):
        ui_index = len(node_ranges) - 1 - i

        hl = "Tag" if i % 2 == 0 else "String"

        mark_id = ctx.nvim.api.buf_set_extmark(
            ctx.buf,
            ctx.ns,
            start,
            0,
            {
                "end_row": end,
                "end_col": -1,
                "strict": False,
                "hl_group": hl,
                "virt_text": [[f" [nid: {nid}]", "Comment"], [f"[{ui_index}]", "Number"]],
                "virt_text_pos": "right_align",
            }
        )
        ctx.extmark_to_nid[mark_id] = nid

    ctx.nvim.api.buf_set_extmark(
        ctx.buf,
        ctx.ns,
        dot_cursor,
        0,
        {
            "end_col": 1,
            "hl_group": "TermCursor"
        }
    )

def render_latex(ctx: RenderContext, result):
    lines = []

    # STACK
    lines.append("STACK")

    for node in result.view.stack:
        lines.append(f"$${node.latex}$$")

    lines.append(".")
    lines.append("")
    lines.append("ENV")

    for name, node in result.view.env.items():
        lines.append(f"$${name} = {node.latex}$$")

    if result.error:
        lines.append("")
        lines.append(f"ERROR: {result.error}")

    ctx.nvim.api.buf_set_lines(
        ctx.buf, 0, -1, False, lines
    )

    stack = result.view.stack
    top_i = len(stack) - 1

    # ctx.nvim.current.window.cursor = (top_i + 3, 1)
    ctx.nvim.api.win_set_cursor(ctx.stack_win, (top_i + 3, 0))

    # -------------------------
    # extmarks
    # -------------------------
    ctx.nvim.api.buf_clear_namespace(ctx.buf, ctx.ns, 0, -1)
    ctx.extmark_to_nid = {}


    # nid marks
    for i, node in enumerate(stack):
        mark_id = ctx.nvim.api.buf_set_extmark(
            ctx.buf,
            ctx.ns,
            i + 1,  # +1 because "STACK" header
            0,
            {
                "virt_text": [[f"nid:{node.nid}", "Comment"]],
                "virt_text_pos": "eol",
                "line_hl_group": "Visual" if i == top_i else None,
            }
        )
        ctx.extmark_to_nid[mark_id] = node.nid
    ctx.nvim.api.buf_set_extmark(
        ctx.buf,
        ctx.ns,
        top_i + 2,  # +1 because "STACK" header
        0,
        {
            "end_col": 1,
            "hl_group": "TermCursor"
        }
    )
