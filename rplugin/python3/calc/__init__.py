from pynvim import plugin, command

from calc.core import State, Command, step, RenderStore
from calc.utils import notify_error, notify_info

from calc.render import build_layout, apply
from calc.parse import parse


class UIState:
    def __init__(self, nvim):
        self.nvim = nvim
        self.buf = self.nvim.api.create_buf(False, True)
        self.ns = self.nvim.api.create_namespace("calc")
        self.extmark_to_nid = {}

@plugin
class CalcPlugin:
    def __init__(self, nvim):
        self.nvim = nvim

        self.state = State()
        self.renderer = RenderStore()

        self.ui: UIState | None = None

        self.last_cmd = None

    def setup_keymaps(self):
        assert self.ui is not None
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
            "s": ":Calc swap<CR>",
            "u": ":Calc undo<CR>",
        }

        for lhs, rhs in maps.items():
            self.nvim.api.buf_set_keymap(
                self.ui.buf,
                "n",
                lhs,
                rhs,
                {"silent": True},
            )

        maps = {
            "i": ":Calc ",
            "ad": ":Calc diff ",
            "vD": ":Calc det<CR>",
        }
        for lhs, rhs in maps.items():
            self.nvim.api.buf_set_keymap(
                self.ui.buf,
                "n",
                lhs,
                rhs,
                {"silent": False},
            )

        for d in "0123456789":
            self.nvim.api.buf_set_keymap(
                    self.ui.buf,
                    "n",
                    d,
                    f":Calc {d}",
                    {"silent": False},
                    )

    def _run(self, cmd: Command):
        win = self.ensure_window()

        result = step(self.state, cmd, self.renderer)

        self.last_cmd = cmd
        assert self.ui is not None
        layout = build_layout(result)
        apply(self.ui, layout, win)

    def ensure_buffer(self):
        if self.ui is None:
            self.ui = UIState(self.nvim)

            self.nvim.api.buf_set_name(self.ui.buf, "CALC")
            self.nvim.api.buf_set_option(self.ui.buf, "filetype", "markdown")

            self.setup_keymaps()

    def ensure_window(self):
        assert self.ui is not None
        buf = self.ui.buf

        for win in self.nvim.api.list_wins():
            if self.nvim.api.win_get_buf(win) == buf:
                return win

        self.nvim.command("vsplit")
        win = self.nvim.current.window

        self.nvim.api.win_set_buf(win, buf)

        return win
    # -------------------------
    # entrypoint
    # -------------------------
    @command("Calc", nargs=1)
    def calc(self, args):
        self.ensure_buffer()

        cmd = parse(args[0])

        self._run(cmd)

        win = self.ensure_window()
        self.nvim.api.set_current_win(win)

    @command("CalcLookup", nargs=0)
    def calc_lookup(self):
        row, _ = self.nvim.current.window.cursor
        row -= 1 # to 0-based

        assert self.ui is not None
        marks = self.nvim.api.buf_get_extmarks(
            self.ui.buf,
            self.ui.ns,
            [row, 0],
            [row, -1],
            {
                "overlap": True
            }
        )

        if not marks:
            self.nvim.out_write("No extmark under cursor\n")
            return

        mark_id = marks[0][0]

        nid = self.ui.extmark_to_nid.get(mark_id)

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
        self.nvim.api.win_close(0, True)
