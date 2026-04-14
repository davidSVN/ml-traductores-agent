from __future__ import annotations

import logging
from pathlib import Path

from langchain_core.tools import tool

from chatbot.config import load_config

logger = logging.getLogger(__name__)

_CHATBOT_DIR = Path(__file__).resolve().parent.parent  # agent/src/chatbot


@tool
async def load_skill(skill_name: str) -> str:
    """Carga las instrucciones detalladas de una habilidad.

    Usa esta herramienta cuando necesites instrucciones paso a paso para:
    - cotizacion: proceso de cotizacion de servicios
    - info_servicios: informacion sobre servicios disponibles
    - seguimiento: seguimiento de clientes existentes

    Args:
        skill_name: Nombre de la habilidad a cargar (sin extension .md)
    """
    config = load_config()
    base_dir = _CHATBOT_DIR / config.skills.base_dir

    skill_path = base_dir / f"{skill_name}.md"

    if not skill_path.exists() and config.skills.fallback_dir:
        skill_path = _CHATBOT_DIR / config.skills.fallback_dir / f"{skill_name}.md"

    if not skill_path.exists():
        available = [p.stem for p in base_dir.glob("*.md")]
        return (
            f"Habilidad '{skill_name}' no encontrada. "
            f"Disponibles: {', '.join(available)}"
        )

    logger.info("skill_loaded", extra={"skill": skill_name})
    return skill_path.read_text(encoding="utf-8")
