local function check()
  vim.health.start("calc.nvim")

  if vim.fn.has("nvim-0.9") ~= 1 then
    vim.health.error("calc.nvim requires Neovim >= 0.9")
    return
  end

  if vim.fn.has("python3") == 0 then
    vim.health.error("Python 3 provider not available. Set g:python3_host_prog or install pynvim")
    return
  end

  vim.cmd("python3 import importlib.util")

  local required = { "pynvim", "sympy" }
  for _, mod in ipairs(required) do
    local found = vim.fn.py3eval("importlib.util.find_spec('" .. mod .. "') is not None")
    if found then
      vim.health.ok("Python module " .. mod .. " found")
    else
      vim.health.error("Python module " .. mod .. " missing", "pip install " .. mod)
    end
  end

  if vim.fn.py3eval("importlib.util.find_spec('latex2sympy2') is not None") then
    vim.health.ok("Python module latex2sympy2 found")
  else
    vim.health.warn("latex2sympy2 not installed — LaTeX push disabled", "pip install latex2sympy2")
  end
end

return { check = check }
