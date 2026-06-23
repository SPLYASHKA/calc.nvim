from typing import Protocol
from pynvim import Nvim

class RenderContext(Protocol):
    nvim: Nvim
    buf: int
    ns: int
    stack_win: object
    extmark_to_nid: dict[int, int]

def render(ctx: RenderContext, result):
    ctx.nvim.api.buf_set_lines(...)
    ctx.buf
    ctx.stack_win

def render(ctx: RenderContext, result):
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

# def render(ctx, result):
#     lines = []
#
#     # -------------------------
#     # STACK HEADER
#     # -------------------------
#     lines.append("STACK")
#
#     stack = result.view.stack
#
#     # будем считать layout-метаданные
#     node_ranges = []  # (start_line, end_line)
#
#     cursor = 1  # после "STACK"
#
#     # -------------------------
#     # STACK CONTENT
#     # -------------------------
#     for node in stack:
#         node_lines = node.latex.splitlines()
#
#         start = cursor
#         lines.extend(node_lines)
#         cursor += len(node_lines)
#         end = cursor - 1
#
#         node_ranges.append((node.nid, start, end))
#
#     # separator
#     lines.append(".")
#     cursor += 1
#
#     # -------------------------
#     # ENV
#     # -------------------------
#     lines.append("")
#     lines.append("ENV")
#     cursor += 2
#
#     for name, node in result.view.env.items():
#         node_lines = node.latex.splitlines()
#
#         lines.extend(node_lines)
#         cursor += len(node_lines)
#
#     # -------------------------
#     # ERROR
#     # -------------------------
#     if result.error:
#         lines.append("")
#         lines.append("ERROR:")
#
#         lines.extend(str(result.error).splitlines())
#
#     # -------------------------
#     # write buffer (IMPORTANT: no \n inside items)
#     # -------------------------
#     for i, l in enumerate(lines):
#         if "\n" in l:
#             ctx.nvim.out_write(f"BAD LINE {i}: {repr(l)}\n")
#     ctx.nvim.api.buf_set_lines(
#         ctx.buf, 0, -1, False, lines
#     )
#
#     # -------------------------
#     # cursor (top of stack)
#     # -------------------------
#     if stack:
#         top_start = node_ranges[-1][1]
#         ctx.nvim.current.window.cursor = (top_start + 1, 0)
#
#     # -------------------------
#     # extmarks
#     # -------------------------
#     ctx.nvim.api.buf_clear_namespace(ctx.buf, ctx.ns, 0, -1)
#     ctx.extmark_to_nid = {}
#
#     top_nid = stack[-1].nid if stack else None
#
#     for nid, start, end in node_ranges:
#         mark_id = ctx.nvim.api.buf_set_extmark(
#             ctx.buf,
#             ctx.ns,
#             start,
#             0,
#             {
#                 "end_row": end,
#                 "line_hl_group": "Visual" if nid == top_nid else None,
#                 "virt_text": [[f"nid:{nid}", "Comment"]],
#                 "virt_text_pos": "eol",
#             }
#         )
#
#         ctx.extmark_to_nid[mark_id] = nid
#
#     # highlight top border line (optional)
#     if stack:
#         ctx.nvim.api.buf_set_extmark(
#             ctx.buf,
#             ctx.ns,
#             node_ranges[-1][1],
#             0,
#             {
#                 "hl_group": "TermCursor",
#             }
#         )
