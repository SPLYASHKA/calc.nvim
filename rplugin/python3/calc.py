from pynvim import plugin, command

from core import State, Command, step, RenderStore
from core.ops import OPERATIONS
from utils import notify_error, notify_info


OP_ALIASES = {
    "+": "add",
    "*": "mul",
    "-": "sub",
    "/": "div",
    "!": "store",
    "@": "subst",
}


@plugin
class CalcPlugin:
    def __init__(self, nvim):
        self.nvim = nvim

        self.state = State()
        self.renderer = RenderStore()

        self.buf = None
        self.stack_win = None
        self.ns = self.nvim.api.create_namespace("calc")
        self.extmark_to_nid = {}
        self.last_cmd = None

    def setup_keymaps(self):
        maps = {
            "+": ":Calc +<CR>",
            "-": ":Calc -<CR>",
            "*": ":Calc *<CR>",
            "/": ":Calc /<CR>",
            "<CR>" : ":Calc dup<CR>",
            "." : ":CalcRepeatLast<CR>",
            "dd": ":Calc drop<CR>",
            "<BS>": ":Calc drop<CR>",
            "!": ":Calc store<CR>",
            "yl": ":CalcCopyLatex<CR>",
            "I": ":CalcLatex<CR>",
        }

        for lhs, rhs in maps.items():
            self.nvim.api.buf_set_keymap(
                self.buf,
                "n",
                lhs,
                rhs,
                {"silent": True},
            )

        maps = {
            "i": ":Calc ",
            "a": ":Calc ",
            "A": ":Calc ",
        }
        for lhs, rhs in maps.items():
            self.nvim.api.buf_set_keymap(
                self.buf,
                "n",
                lhs,
                rhs,
                {"silent": False},
            )

        for d in "0123456789":
            self.nvim.api.buf_set_keymap(
                    self.buf,
                    "n",
                    d,
                    f":Calc {d}",
                    {"silent": False},
                    )

    def _run(self, cmd: Command):
        result = step(self.state, cmd, self.renderer)

        self.last_cmd = cmd
        self.render(result)

    def ensure_buffer(self):
        if self.buf is None:
            self.buf = self.nvim.api.create_buf(False, True)
            self.nvim.api.buf_set_name(self.buf, "CALC")

            # UI semantics
            self.nvim.api.buf_set_option(self.buf, "filetype", "markdown")
            self.nvim.api.buf_set_option(self.buf, "buftype", "nofile")
            self.nvim.api.buf_set_option(self.buf, "swapfile", False)

            # 🔒 protection layer
            # self.nvim.api.buf_set_option(self.buf, "modifiable", False)
            # self.nvim.api.buf_set_option(self.buf, "readonly", True)

            # open split
            self.nvim.command("vsplit")
            self.stack_win = self.nvim.current.window
            self.nvim.api.win_set_buf(0, self.buf)   #         self.nvim.api.win_set_buf(0, self.buf)

            self.setup_keymaps()
    # -------------------------
    # latex wrapper
    # -------------------------
    def latex(self, expr: str, tag: int | None = None) -> str:
        if tag is None:
            return f"$${expr}$$"
        return f"$${expr} \\tag{{{tag}}}$$"

    # -------------------------
    # parsing
    # -------------------------
    def parse(self, token: str) -> Command:
        token = token.strip()

        if token == "undo":
            return Command(op="__undo__", args={})

        if token in OP_ALIASES:
            return Command(op=OP_ALIASES[token], args={})

        if token in OPERATIONS:
            return Command(op=token, args={})

        return Command(op="push", args={"value": token})

    # -------------------------
    # entrypoint
    # -------------------------
    @command("Calc", nargs=1)
    def calc(self, args):
        self.ensure_buffer()

        cmd = self.parse(args[0])

        self._run(cmd)
    # -------------------------
    # render to buffer
    # -------------------------
    def render(self, result):
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

        self.nvim.api.buf_set_lines(
            self.buf, 0, -1, False, lines
        )

        stack = result.view.stack
        top_i = len(stack) - 1

        # self.nvim.current.window.cursor = (top_i + 3, 1)
        self.nvim.api.win_set_cursor(self.stack_win, (top_i + 3, 0))

        # -------------------------
        # extmarks
        # -------------------------
        self.nvim.api.buf_clear_namespace(self.buf, self.ns, 0, -1)
        self.extmark_to_nid = {}


        # nid marks
        for i, node in enumerate(stack):
            mark_id = self.nvim.api.buf_set_extmark(
                self.buf,
                self.ns,
                i + 1,  # +1 because "STACK" header
                0,
                {
                    "virt_text": [[f"nid:{node.nid}", "Comment"]],
                    "virt_text_pos": "eol",
                    "line_hl_group": "Visual" if i == top_i else None,
                }
            )
            self.extmark_to_nid[mark_id] = node.nid
        self.nvim.api.buf_set_extmark(
            self.buf,
            self.ns,
            top_i + 2,  # +1 because "STACK" header
            0,
            {
                "end_col": 1,
                "hl_group": "TermCursor"
            }
        )

    # def render(self, result):
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
    #             self.nvim.out_write(f"BAD LINE {i}: {repr(l)}\n")
    #     self.nvim.api.buf_set_lines(
    #         self.buf, 0, -1, False, lines
    #     )
    #
    #     # -------------------------
    #     # cursor (top of stack)
    #     # -------------------------
    #     if stack:
    #         top_start = node_ranges[-1][1]
    #         self.nvim.current.window.cursor = (top_start + 1, 0)
    #
    #     # -------------------------
    #     # extmarks
    #     # -------------------------
    #     self.nvim.api.buf_clear_namespace(self.buf, self.ns, 0, -1)
    #     self.extmark_to_nid = {}
    #
    #     top_nid = stack[-1].nid if stack else None
    #
    #     for nid, start, end in node_ranges:
    #         mark_id = self.nvim.api.buf_set_extmark(
    #             self.buf,
    #             self.ns,
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
    #         self.extmark_to_nid[mark_id] = nid
    #
    #     # highlight top border line (optional)
    #     if stack:
    #         self.nvim.api.buf_set_extmark(
    #             self.buf,
    #             self.ns,
    #             node_ranges[-1][1],
    #             0,
    #             {
    #                 "hl_group": "TermCursor",
    #             }
    #         )

    @command("CalcLookup", nargs=0)
    def calc_lookup(self):
        row, _ = self.nvim.current.window.cursor
        row -= 1 # to 0-based

        marks = self.nvim.api.buf_get_extmarks(
            self.buf,
            self.ns,
            [row, 0],
            [row, -1],
            {}
        )

        if not marks:
            self.nvim.out_write("No extmark under cursor\n")
            return

        mark_id = marks[0][0]

        nid = self.extmark_to_nid.get(mark_id)

        if nid is None:
            self.nvim.out_write(f"No nid found for mark {mark_id}\n")
            return

        self.nvim.out_write(f"NID: {nid}\n")
        return nid

    @command("CalcCopyLatex", nargs=0)
    def calc_copy_latex(self):
        nid = self.calc_lookup()

        if nid is None:
            return

        # NOTE: не очень хорошо, что напрямую с renderer взаимодействую
        latex = self.renderer.get(self.state, nid).latex

        self.nvim.funcs.setreg('@', latex) # nvim clipboard
        self.nvim.funcs.setreg('+', latex) # system clipboard

        notify_info(self.nvim, "LaTex copied: " + latex)

    @command("CalcPushLatexVisual", range="")
    def calc_latex(self, _):
        # lineno_begin, colno_begin = self.nvim.api.buf_get_mark(0, "<")
        # lineno_end, colno_end = self.nvim.api.buf_get_mark(0, ">")
        _, lineno_begin, colno_begin, _ = self.nvim.funcs.getpos("'<")
        _, lineno_end, colno_end, _ = self.nvim.funcs.getpos("'>")

        if lineno_begin == 0 or colno_begin == 0 or lineno_end == 0 or colno_end == 0:
            notify_error(self.nvim, "No visual selection found")
            return

        span = (
            (
                lineno_begin - 1,
                min(colno_begin, len(self.nvim.funcs.getline(lineno_begin))) - 1,
            ),
            (
                lineno_end - 1,
                min(colno_end, len(self.nvim.funcs.getline(lineno_end))),
            ),
        )

        self._push_latex(span)

    def _push_latex(self, pos: tuple[tuple[int, int], tuple[int, int]]) -> None:
        value = self._extract_value(pos)

        self.ensure_buffer()

        cmd = Command(op="push", args={"value": value, "format": "latex"})

        self._run(cmd)

    def _extract_value(self, pos: tuple[tuple[int, int], tuple[int, int]]) -> str:
        (r1, c1), (r2, c2) = pos

        lines = self.nvim.funcs.nvim_buf_get_lines(
            0,
            r1,
            r2 + 1,
            False,
        )

        if not lines:
            return ""

        if len(lines) == 1:
            return lines[0][c1:c2]

        return "\n".join(
            [lines[0][c1:]]
            + lines[1:-1]
            + [lines[-1][:c2]]
        )
    @command("CalcRepeatLast", nargs=0)
    def repeat_last(self):
        if self.last_cmd is None:
            self.nvim.out_write("No previous command\n")
            return

        self._run(self.last_cmd)

    @command("CalcLatex", nargs=0)
    def open_latex_float(self):
        buf = self.nvim.api.create_buf(False, True)

        self.nvim.api.buf_set_option(buf, "filetype", "tex")

        template = [
            "$$",
            "",
            "$$"
        ]

        self.nvim.api.buf_set_lines(buf, 0, -1, False, template)

        width = 60
        height = 10

        win = self.nvim.api.open_win(
            buf,
            True,
            {
                "relative": "editor",
                "width": width,
                "height": height,
                "row": 5,
                "col": 10,
                "style": "minimal",
                "border": "rounded",
            }
        )

        self.nvim.api.win_set_cursor(win, (2, 0))

        self.nvim.api.buf_set_keymap(buf, "n", "<C-c>", "<Esc>:bd!<CR>", {"silent": True})
        # ENTER = commit
        self.nvim.api.buf_set_keymap(
            buf,
            "n",
            "<CR>",
            ":CalcCommitLatex<CR>",
            {"silent": True}
            )

        self.nvim.command("startinsert")

    @command("CalcCommitLatex", nargs=0)
    def calc_commit_latex(self):
        lines = self.nvim.api.buf_get_lines(0, 0, -1, False)
        latex = "\n".join(lines)

        cmd = Command(
            op="push",
            args={"value": latex, "format": "latex"}
        )

        self._run(cmd)

        # close float
        self.nvim.api.win_close(0, True)
