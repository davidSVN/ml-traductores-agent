from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)

_CHATBOT_DIR = Path(__file__).resolve().parent  # agent/src/chatbot


@dataclass(frozen=True)
class ModelConfig:
    provider: str
    name: str
    temperature: float = 0.3
    max_tokens: int | None = None


@dataclass(frozen=True)
class PromptConfig:
    file: str  # relative to _SRC_DIR
    model: ModelConfig


@dataclass(frozen=True)
class SkillsConfig:
    base_dir: str
    fallback_dir: str | None = None


@dataclass(frozen=True)
class ChatbotConfig:
    prompts: dict[str, PromptConfig]
    skills: SkillsConfig


def load_config(path: Path | None = None) -> ChatbotConfig:
    """Load and parse chatbot_config.yaml into typed dataclasses."""
    if path is None:
        path = _CHATBOT_DIR / "chatbot_config.yaml"

    raw = yaml.safe_load(path.read_text(encoding="utf-8"))

    prompts = {}
    for key, val in raw["prompts"].items():
        prompts[key] = PromptConfig(
            file=val["file"],
            model=ModelConfig(**val["model"]),
        )

    skills_raw = raw.get("skills", {})
    skills = SkillsConfig(
        base_dir=skills_raw.get("base_dir", "chatbot/skills"),
        fallback_dir=skills_raw.get("fallback_dir"),
    )

    return ChatbotConfig(prompts=prompts, skills=skills)
