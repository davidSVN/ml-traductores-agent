"""Tools for the chatbot agent.

All tools are registered in the `tools` list and automatically
bound to the LLM via bind_tools().
"""

from .create_quote import create_quote
from .get_pricing import get_pricing
from .get_services import get_services
from .load_skill import load_skill

tools: list = [
    load_skill,
    get_pricing,
    create_quote,
    get_services,
]
