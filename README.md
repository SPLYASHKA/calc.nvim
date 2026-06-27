# calc.nvim

**Work in progress.** Interactive symbolic RPN calculator for Neovim powered by [SymPy](https://www.sympy.org/).

## Features

- RPN stack-based symbolic mathematics
- LaTeX input and output via [latex2sympy2](https://github.com/OrangeX4/latex2sympy)
- Environment variables for storing and recalling expressions
- Stack operations: `dup`, `drop`, `swap`, `pick`, `undo`
- Calculus: differentiation, determinant
- Algebra: expand, factor
- Implicit multiplication support (`2x`, `(a-1)(a+1)`)
- Rich display with virtual text, extmarks, and LaTeX conceal
- Undo history for the stack
- Inline help (`?`)
- Healthcheck (`:checkhealth calc`)

## Requirements

- Neovim 0.9+
- Python 3 with `pynvim`, `sympy`
- `latex2sympy2` (optional, for LaTeX push)

## Installation

### [lazy.nvim](https://github.com/folke/lazy.nvim)

```lua
{
  "splyashka/calc.nvim",
  build = ":UpdateRemotePlugins",
  init = function()
    vim.g.python3_host_prog = vim.fn.expand("~/.virtualenvs/neovim/bin") .. "/python3"
  end,
  keys = {
    { "<leader>cl", ":CalcPushLatexVisual<CR>", desc = "Push LaTeX selection", mode = "x" },
  },
}
```

Run `:Calc` to open the calculator window. Run `:Calc` again to close it.

> **Note:** Make sure your Python 3 host (set via `g:python3_host_prog`) has `pynvim` and `sympy`
> installed. `latex2sympy2` is optional (needed for LaTeX push). Run `:checkhealth calc` after
> installation to verify.

## Usage

### Commands

| Command | Effect |
|---|---|
| `:Calc <op>` | Execute operation (open window if closed) |
| `:CalcToggle` | Open/close the calculator window |
| `:CalcHelp` | Show help float window |
| `+`, `-`, `*`, `/` | Pop top 2, push result |
| `dup` | Duplicate top of stack |
| `drop` | Remove top of stack |
| `swap` | Swap top 2 elements |
| `pick N` | Push copy of Nth element (0-indexed from top) |
| `undo` | Restore previous stack state |
| `!` | Store: pop a Symbol (name), pop next value, save to env |
| `@` | Substitute: pop a Symbol, pop an expression, substitute from env |
| `eval` | Substitute all env variables into the top expression |
| `diff sym1 ...` | Differentiate top expression wrt given symbols |
| `expand` | Expand top expression |
| `factor` | Factor top expression |
| `det` | Determinant of top expression (must be a matrix) |
| *(any other value)* | Push it as a SymPy expression |

### Buffer keymaps (normal mode)

| Key | Action |
|---|---|
| `+`, `-`, `*`, `/` | Add, subtract, multiply, divide |
| `<CR>` | Duplicate top |
| `.` | Repeat last command |
| `dd` / `<BS>` | Drop top |
| `!` | Store in env |
| `yl` | Copy LaTeX of expression under cursor |
| `I` | Open floating LaTeX input window |
| `s` | Swap top 2 |
| `u` | Undo |
| `?` | Show help |
| `0` – `9` | Push digit |
| `i` | Enter `:Calc` command |
| `ad` | Enter `:Calc diff` (differentiate) |
| `ax` | Expand |
| `af` | Factor |
| `vD` | Compute determinant |

### Visual mode

| Key | Action |
|---|---|
| `<leader>cl` | Push visual selection as LaTeX |

## Examples

**Differentiate** — type `:Calc diff x`, or press `ad` and type `x`:

```
x^2 + 3*x  →  2*x + 3
```

**Matrix determinant** — push a sympy matrix, press `vD`:

```
Matrix([[1, 2], [3, 4]])  →  -2
```

**Expand and factor** — press `ax` or `af`:

```
(x-1)*(x+1)  →  x^2 - 1
x^2 - 1     →  (x-1)*(x+1)
```

**Store and recall** — push a value, then push a symbol on top and press `!`:

```
42       — push value
ans      — push symbol
!        — store (pops symbol then value) → env["ans"] = 42

ans + 1  — push expression
ans      — push symbol
@        — subst (pops symbol then expression) → 43
```

**LaTeX input** — press `I`, type LaTeX in the float buffer, press `<CR>` to commit:

```
\frac{d}{dx} x^2  →  2*x
```

## Roadmap

- [ ] `K` hover for info about the expression under cursor
- [ ] Configurable keymaps

## License

MIT
