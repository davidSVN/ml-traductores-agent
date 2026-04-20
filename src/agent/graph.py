import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode

from src.agent.nodes import chatbot_node, detect_phase_node, lookup_contact_node, update_state_node
from src.agent.state import AgentState
from src.tools.db_cliente import buscar_cliente, crear_cliente, crear_contacto, actualizar_contacto, actualizar_cliente
from src.tools.db_conversacion import marcar_revisar
from src.tools.db_cotizacion import (
    actualizar_cotizacion, calcular_cotizacion, crear_solicitud, enviar_cotizacion
)
from src.tools.db_servicios import consultar_historial, consultar_tarifas, listar_servicios

logger = logging.getLogger(__name__)

ALL_TOOLS = [
    listar_servicios,
    buscar_cliente,
    crear_cliente,
    crear_contacto,
    actualizar_contacto,
    actualizar_cliente,
    consultar_historial,
    consultar_tarifas,
    calcular_cotizacion,
    enviar_cotizacion,
    crear_solicitud,
    actualizar_cotizacion,
    marcar_revisar,
]


def _should_continue(state: AgentState) -> str:
    last = state["messages"][-1]
    if getattr(last, "tool_calls", None):
        return "tools"
    return END


def _build_workflow(checkpointer):
    workflow = StateGraph(AgentState)
    workflow.add_node("detect_phase", detect_phase_node)
    workflow.add_node("lookup_contact", lookup_contact_node)
    workflow.add_node("chatbot", chatbot_node)
    workflow.add_node("tools", ToolNode(ALL_TOOLS))
    workflow.add_node("update_state", update_state_node)

    workflow.set_entry_point("detect_phase")
    workflow.add_edge("detect_phase", "lookup_contact")
    workflow.add_edge("lookup_contact", "chatbot")
    workflow.add_conditional_edges(
        "chatbot",
        _should_continue,
        {"tools": "tools", END: END},
    )
    workflow.add_edge("tools", "update_state")
    workflow.add_edge("update_state", "chatbot")

    return workflow.compile(checkpointer=checkpointer)


@asynccontextmanager
async def build_graph(database_url: str) -> AsyncIterator:
    """
    Context manager que mantiene vivo el checkpointer PostgreSQL
    durante toda la vida de la aplicación FastAPI.

    AsyncPostgresSaver requiere psycopg (no asyncpg).
    URL: postgresql+asyncpg:// → postgresql://

    Usa AsyncConnectionPool para reconexión automática si RDS corta la conexión.
    """
    from psycopg_pool import AsyncConnectionPool

    psycopg_url = database_url.replace("postgresql+asyncpg://", "postgresql://")

    async with AsyncConnectionPool(
        conninfo=psycopg_url,
        min_size=1,
        max_size=5,
        kwargs={"autocommit": True, "prepare_threshold": 0},
    ) as pool:
        checkpointer = AsyncPostgresSaver(pool)
        await checkpointer.setup()
        logger.info("LangGraph checkpointer initialized (PostgreSQL pool)")

        graph = _build_workflow(checkpointer)
        logger.info("LangGraph compiled: detect_phase → chatbot ⇌ tools → update_state")
        yield graph
