from dataclasses import dataclass

@dataclass(frozen=True)
class ViewNode:
    nid: int
    text: str
    pretty: str
    latex: str


@dataclass(frozen=True)
class ViewState:
    stack: list[ViewNode]
    env: dict[str, ViewNode]

from .render import RenderStore
from .state import State
from .view import ViewNode, ViewState


def build_view(state: State, renderer: RenderStore) -> ViewState:
    stack = [
        ViewNode(
            nid=nid,
            **renderer.get(state, nid).__dict__
        )
        for nid in state.stack
    ]

    env = {
        k: ViewNode(
            nid=nid,
            **renderer.get(state, nid).__dict__
        )
        for k, nid in state.env.items()
    }

    return ViewState(stack=stack, env=env)

def view(state: State, renderer: RenderStore):
    return build_view(state, renderer)
