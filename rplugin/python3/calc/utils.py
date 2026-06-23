from pynvim import Nvim

def _notify(nvim: Nvim, msg: str, log_level: str) -> None:
    nvim.exec_lua(
        """
        local msg = ...
        local level = ...

        vim.schedule(function()
            vim.notify(msg, vim.log.levels[level], {})
        end)
        """,
        f"[Calc] {msg}",
        log_level,
    )

def notify_info(nvim: Nvim, msg: str) -> None:
    """Use the vim.notify API to display an info message."""
    _notify(nvim, msg, "INFO")


def notify_warn(nvim: Nvim, msg: str) -> None:
    """Use the vim.notify API to display a warning message."""
    _notify(nvim, msg, "WARN")


def notify_error(nvim: Nvim, msg: str) -> None:
    """Use the vim.notify API to display an error message."""
    _notify(nvim, msg, "ERROR")
