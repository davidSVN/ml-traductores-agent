from __future__ import annotations

import logging
from functools import lru_cache
from pathlib import Path

from langchain_openai import ChatOpenAI

from .config import ChatbotConfig, ModelConfig

logger = logging.getLogger(__name__)

_CHATBOT_DIR = Path(__file__).resolve().parent  # agent/src/chatbot


def _build_llm(model_cfg: ModelConfig):
    """Factory: build a LangChain ChatModel from config."""
    kwargs: dict = {"model": model_cfg.name, "temperature": model_cfg.temperature}
    if model_cfg.max_tokens is not None:
        kwargs["max_tokens"] = model_cfg.max_tokens

    if model_cfg.provider == "openai":
        return ChatOpenAI(**kwargs)

    # Extensible: add providers here
    # if model_cfg.provider == "anthropic":
    #     from langchain_anthropic import ChatAnthropic
    #     return ChatAnthropic(**kwargs)

    raise ValueError(f"Unknown model provider: {model_cfg.provider}")


@lru_cache(maxsize=16)
def _read_prompt_file(abs_path: str) -> str:
    return Path(abs_path).read_text(encoding="utf-8")


def load_prompt(config: ChatbotConfig, prompt_key: str) -> tuple[str, object]:
    """Return (prompt_text, llm) for the given prompt key."""
    prompt_cfg = config.prompts[prompt_key]
    abs_path = _CHATBOT_DIR / prompt_cfg.file
    prompt_text = _read_prompt_file(str(abs_path))
    llm = _build_llm(prompt_cfg.model)
    return prompt_text, llm
