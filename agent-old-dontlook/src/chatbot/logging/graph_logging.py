from __future__ import annotations

import asyncio
import functools
import logging
import time
import uuid
from typing import Any, Callable, TypeVar

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


def log_node(node_name: str) -> Callable[[F], F]:
    def _run_id(state: Any) -> str:
        if state is None:
            return ""
        if isinstance(state, dict):
            return str(state.get("graph_run_id", "")) if state.get("graph_run_id") else ""
        return str(getattr(state, "graph_run_id", "") or "")

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def sync_wrapper(state: Any) -> Any:
            graph_run_id = _run_id(state)
            logger.info("node_started", extra={"node": node_name, "graph_run_id": graph_run_id})
            t0 = time.perf_counter()
            try:
                result = func(state)
                duration_ms = int((time.perf_counter() - t0) * 1000)
                logger.info("node_completed", extra={"node": node_name, "graph_run_id": graph_run_id, "duration_ms": duration_ms})
                return result
            except Exception:
                duration_ms = int((time.perf_counter() - t0) * 1000)
                logger.exception("node_failed", extra={"node": node_name, "graph_run_id": graph_run_id, "duration_ms": duration_ms})
                raise

        @functools.wraps(func)
        async def async_wrapper(state: Any) -> Any:
            graph_run_id = _run_id(state)
            logger.info("node_started", extra={"node": node_name, "graph_run_id": graph_run_id})
            t0 = time.perf_counter()
            try:
                result = await func(state)
                duration_ms = int((time.perf_counter() - t0) * 1000)
                logger.info("node_completed", extra={"node": node_name, "graph_run_id": graph_run_id, "duration_ms": duration_ms})
                return result
            except Exception:
                duration_ms = int((time.perf_counter() - t0) * 1000)
                logger.exception("node_failed", extra={"node": node_name, "graph_run_id": graph_run_id, "duration_ms": duration_ms})
                raise

        if asyncio.iscoroutinefunction(func):
            return async_wrapper  # type: ignore[return-value]
        return sync_wrapper  # type: ignore[return-value]

    return decorator


class _GraphWrapper:
    def __init__(self, graph: Any, graph_name: str) -> None:
        self.__dict__["_graph"] = graph
        self.__dict__["_graph_name"] = graph_name

    def __getattr__(self, name: str) -> Any:
        return getattr(self._graph, name)

    def invoke(self, input: Any, config: Any = None, **kwargs: Any) -> Any:
        run_id = str(uuid.uuid4())[:12]
        logger.info("graph_run_started", extra={"graph_name": self._graph_name, "graph_run_id": run_id, "input_chars": len(str(input)) if input else 0})
        t0 = time.perf_counter()
        try:
            result = self._graph.invoke(input, config=config, **kwargs)
            duration_ms = int((time.perf_counter() - t0) * 1000)
            logger.info("graph_run_completed", extra={"graph_name": self._graph_name, "graph_run_id": run_id, "duration_ms": duration_ms, "output_chars": len(str(result)) if result else 0})
            return result
        except Exception:
            duration_ms = int((time.perf_counter() - t0) * 1000)
            logger.exception("graph_run_failed", extra={"graph_name": self._graph_name, "graph_run_id": run_id, "duration_ms": duration_ms})
            raise

    async def ainvoke(self, input: Any, config: Any = None, **kwargs: Any) -> Any:
        run_id = str(uuid.uuid4())[:12]
        logger.info("graph_run_started", extra={"graph_name": self._graph_name, "graph_run_id": run_id, "input_chars": len(str(input)) if input else 0})
        t0 = time.perf_counter()
        try:
            result = await self._graph.ainvoke(input, config=config, **kwargs)
            duration_ms = int((time.perf_counter() - t0) * 1000)
            logger.info("graph_run_completed", extra={"graph_name": self._graph_name, "graph_run_id": run_id, "duration_ms": duration_ms, "output_chars": len(str(result)) if result else 0})
            return result
        except Exception:
            duration_ms = int((time.perf_counter() - t0) * 1000)
            logger.exception("graph_run_failed", extra={"graph_name": self._graph_name, "graph_run_id": run_id, "duration_ms": duration_ms})
            raise


def wrap_graph(compiled_graph: Any, graph_name: str) -> Any:
    return _GraphWrapper(compiled_graph, graph_name)
