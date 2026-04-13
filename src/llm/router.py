from src.llm.anthropic_provider import AnthropicProvider
from src.llm.schemas import LLMResponse, ToolDefinition

# Future: from src.llm.openai_provider import OpenAIProvider


class LLMRouter:
    def __init__(self, provider: str = "anthropic") -> None:
        if provider == "anthropic":
            self._provider = AnthropicProvider()
        # elif provider == "openai":
        #     self._provider = OpenAIProvider()
        else:
            raise ValueError(f"Unknown provider: {provider}")

    async def send_message(
        self,
        messages: list[dict],
        system_prompt: str,
        tools: list[ToolDefinition] | None = None,
    ) -> LLMResponse:
        return await self._provider.send_message(messages, system_prompt, tools)
