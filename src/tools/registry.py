import logging
from collections.abc import Callable
from typing import Any

from langsmith import traceable

from src.llm.schemas import ToolDefinition

logger = logging.getLogger(__name__)

_REGISTRY: dict[str, tuple[Callable, ToolDefinition]] = {}


def register_tool(name: str, description: str, parameters: dict) -> Callable:
    def decorator(func: Callable) -> Callable:
        _REGISTRY[name] = (func, ToolDefinition(name=name, description=description, parameters=parameters))
        logger.debug(f"Tool registered: {name}")
        return func

    return decorator


def get_tool_definitions(names: list[str] | None = None) -> list[ToolDefinition]:
    if names is None:
        return [td for _, td in _REGISTRY.values()]
    return [_REGISTRY[n][1] for n in names if n in _REGISTRY]


@traceable(name="execute_tool", run_type="tool")
async def execute_tool(name: str, arguments: dict, **extra: Any) -> Any:
    if name not in _REGISTRY:
        raise ValueError(f"Tool not found: {name}")
    func, _ = _REGISTRY[name]
    return await func(**arguments, **extra)


def list_tools() -> list[str]:
    return list(_REGISTRY.keys())
