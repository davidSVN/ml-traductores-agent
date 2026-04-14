from contextvars import ContextVar
from logging import Filter
from typing import Any

_session_id: ContextVar[str] = ContextVar("session_id", default="")
_request_id: ContextVar[str] = ContextVar("request_id", default="")
_graph_run_id: ContextVar[str] = ContextVar("graph_run_id", default="")
_thread_id: ContextVar[str] = ContextVar("thread_id", default="")
_node: ContextVar[str] = ContextVar("node", default="")
_channel: ContextVar[str] = ContextVar("channel", default="")


def set_context(
    *,
    session_id: str = "",
    request_id: str = "",
    graph_run_id: str = "",
    thread_id: str = "",
    node: str = "",
    channel: str = "",
) -> None:
    if session_id:
        _session_id.set(session_id)
    if request_id:
        _request_id.set(request_id)
    if graph_run_id:
        _graph_run_id.set(graph_run_id)
    if thread_id:
        _thread_id.set(thread_id)
    if node:
        _node.set(node)
    if channel:
        _channel.set(channel)


def get_context() -> dict[str, Any]:
    return {
        "session_id": _session_id.get() or None,
        "request_id": _request_id.get() or None,
        "graph_run_id": _graph_run_id.get() or None,
        "thread_id": _thread_id.get() or None,
        "node": _node.get() or None,
        "channel": _channel.get() or None,
    }


def clear_context() -> None:
    _session_id.set("")
    _request_id.set("")
    _graph_run_id.set("")
    _thread_id.set("")
    _node.set("")
    _channel.set("")


class LoggingContextFilter(Filter):
    def filter(self, record: Any) -> bool:
        ctx = get_context()
        for key, val in ctx.items():
            if val is not None and not hasattr(record, key):
                setattr(record, key, val)
        return True
