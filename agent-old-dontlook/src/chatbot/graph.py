import sys
from pathlib import Path

# LangGraph loads this file directly, so we need to ensure
# the src directory is on sys.path for absolute imports.
_src_dir = str(Path(__file__).resolve().parent.parent)
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

from chatbot.logging import setup_logging
from chatbot.logging.context import set_context
from chatbot.logging.graph_logging import log_node

setup_logging()
set_context(node="chatbot")

from langgraph.graph import StateGraph
from langgraph.prebuilt import ToolNode

from chatbot.nodes import chatbot_node
from chatbot.state import State
from chatbot.tools import tools


def should_continue(state: State) -> str:
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return "__end__"


workflow = StateGraph(State)

workflow.add_node("chatbot", log_node("chatbot")(chatbot_node))

if tools:
    workflow.add_node("tools", ToolNode(tools))
    workflow.add_conditional_edges("chatbot", should_continue, {"tools": "tools", "__end__": "__end__"})
    workflow.add_edge("tools", "chatbot")
else:
    workflow.add_edge("chatbot", "__end__")

workflow.set_entry_point("chatbot")

graph = workflow.compile()
