from langchain_core.messages import SystemMessage

from chatbot.config import load_config
from chatbot.prompt_loader import load_prompt
from chatbot.state import State
from chatbot.tools import tools

_config = load_config()
_system_prompt_text, _llm = load_prompt(_config, "chatbot_system")

if tools:
    _llm_with_tools = _llm.bind_tools(tools)
else:
    _llm_with_tools = _llm


async def chatbot_node(state: State) -> dict:
    system = SystemMessage(content=_system_prompt_text)
    response = await _llm_with_tools.ainvoke([system] + state["messages"])
    return {"messages": [response]}
