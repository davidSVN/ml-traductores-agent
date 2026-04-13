import json
import logging
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from src.llm.router import LLMRouter
from src.llm.schemas import LLMResponse, ToolDefinition
from src.tools.registry import execute_tool, get_tool_definitions

logger = logging.getLogger(__name__)

SKILLS_DIR = Path(__file__).parent.parent / "skills"

PHASE_CONFIG: dict[str, dict] = {
    "inicial": {
        "skills": ["personalidad.md", "recopilacion.md"],
        "tools": ["buscar_cliente", "crear_cliente"],
    }
}


class AgentOrchestrator:
    def __init__(self) -> None:
        self.llm = LLMRouter(provider="anthropic")

    async def handle_message(
        self,
        conversation_history: list[dict],
        db: AsyncSession,
        phase: str = "inicial",
    ) -> str:
        config = PHASE_CONFIG.get(phase, PHASE_CONFIG["inicial"])
        system_prompt = self._load_skills(phase)
        tool_defs = get_tool_definitions(config["tools"])

        response = await self.llm.send_message(
            messages=conversation_history,
            system_prompt=system_prompt,
            tools=tool_defs,
        )

        if response.tool_calls:
            return await self._handle_tool_calls(
                response=response,
                history=conversation_history,
                system_prompt=system_prompt,
                tool_defs=tool_defs,
                db=db,
            )

        return response.content

    async def _handle_tool_calls(
        self,
        response: LLMResponse,
        history: list[dict],
        system_prompt: str,
        tool_defs: list[ToolDefinition],
        db: AsyncSession,
        max_iterations: int = 5,
    ) -> str:
        current_history = list(history)

        for _ in range(max_iterations):
            if not response.tool_calls:
                break

            # Add assistant's tool_use turn to history
            current_history.append({
                "role": "assistant",
                "content": response.content or "",
            })

            # Execute each tool and append results
            for tc in response.tool_calls:
                logger.info(f"Executing tool: {tc.name} args={tc.arguments}")
                try:
                    result = await execute_tool(tc.name, tc.arguments, db=db)
                except Exception as e:
                    logger.error(f"Tool {tc.name} failed: {e}")
                    result = {"error": str(e)}

                current_history.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": json.dumps(result, ensure_ascii=False, default=str),
                })

            # Re-call LLM with tool results
            response = await self.llm.send_message(
                messages=current_history,
                system_prompt=system_prompt,
                tools=tool_defs,
            )

        return response.content

    def _load_skills(self, phase: str) -> str:
        config = PHASE_CONFIG.get(phase, PHASE_CONFIG["inicial"])
        parts: list[str] = []
        for filename in config["skills"]:
            skill_path = SKILLS_DIR / filename
            if skill_path.exists():
                parts.append(skill_path.read_text(encoding="utf-8"))
            else:
                logger.warning(f"Skill file not found: {skill_path}")
        return "\n\n---\n\n".join(parts)
