from pynvim import plugin, command

from core import State, Command, step, RenderStore
from core.ops import OPERATIONS


OP_ALIASES = {
    "+": "add",
    "*": "mul",
    "-": "sub",
    "!": "store",
    "@": "subst",
}


@plugin
class RpnPlugin:
    def __init__(self, nvim):
        self.nvim = nvim

        self.state = State()
        self.renderer = RenderStore()

        self.buf = None
        self.ns = self.nvim.api.create_namespace("rpn")
        self.extmark_to_nid = {}

    def setup_keymaps(self):
        maps = {
            "+": ":Rpn +<CR>",
            "-": ":Rpn -<CR>",
            "*": ":Rpn *<CR>",
            "/": ":Rpn /<CR>",
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
            "i": ":Rpn ",
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
                    f":Rpn {d}",
                    {"silent": False},
                    )
    def ensure_buffer(self):
        if self.buf is None:
            self.buf = self.nvim.api.create_buf(False, True)
            self.nvim.api.buf_set_name(self.buf, "RPN")

            # UI semantics
            self.nvim.api.buf_set_option(self.buf, "filetype", "markdown")
            self.nvim.api.buf_set_option(self.buf, "buftype", "nofile")
            self.nvim.api.buf_set_option(self.buf, "swapfile", False)

            # 🔒 protection layer
            # self.nvim.api.buf_set_option(self.buf, "modifiable", False)
            self.nvim.api.buf_set_option(self.buf, "readonly", True)

            # open split
            self.nvim.command("vsplit")
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
    @command("Rpn", nargs=1)
    def rpn(self, args):
        self.ensure_buffer()

        cmd = self.parse(args[0])

        result = step(
            self.state,
            cmd,
            self.renderer,
        )

        self.render(result)

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

        self.nvim.current.window.cursor = (top_i + 3, 1)

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

    @command("RpnLookup", nargs=0)
    def rpn_lookup(self):
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
