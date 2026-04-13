import logging
import os

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tracers import LangChainTracer

from src.config import get_settings
from src.llm.schemas import LLMResponse, ToolCall, ToolDefinition

logger = logging.getLogger(__name__)

settings = get_settings()


class AnthropicProvider:
    def __init__(self) -> None:
        # Configure LangSmith tracing — set both naming conventions
        # langchain-anthropic checks LANGCHAIN_* vars; newer langsmith SDK checks LANGSMITH_*
        project = settings.langsmith_project.strip('"').strip("'")
        os.environ["LANGCHAIN_TRACING_V2"] = settings.langsmith_tracing
        os.environ["LANGCHAIN_API_KEY"] = settings.langsmith_api_key
        os.environ["LANGCHAIN_PROJECT"] = project
        os.environ["LANGCHAIN_ENDPOINT"] = settings.langsmith_endpoint
        os.environ["LANGSMITH_TRACING"] = settings.langsmith_tracing
        os.environ["LANGSMITH_API_KEY"] = settings.langsmith_api_key
        os.environ["LANGSMITH_PROJECT"] = project
        os.environ["LANGSMITH_ENDPOINT"] = settings.langsmith_endpoint

        self.llm = ChatAnthropic(
            model="claude-sonnet-4-6",
            api_key=settings.anthropic_api_key,
            max_tokens=4096,
        )

    async def send_message(
        self,
        messages: list[dict],
        system_prompt: str,
        tools: list[ToolDefinition] | None = None,
    ) -> LLMResponse:
        lc_messages = [SystemMessage(content=system_prompt)]

        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            if role == "user":
                lc_messages.append(HumanMessage(content=content))
            elif role == "assistant":
                lc_messages.append(AIMessage(content=content))
            elif role == "tool":
                lc_messages.append(
                    ToolMessage(
                        content=str(content),
                        tool_call_id=msg.get("tool_call_id", ""),
                    )
                )

        llm = self.llm
        if tools:
            tool_schemas = [
                {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.parameters,
                }
                for t in tools
            ]
            llm = self.llm.bind_tools(tool_schemas)

        tracer = LangChainTracer(project_name=settings.langsmith_project.strip('"').strip("'"))
        response = await llm.ainvoke(lc_messages, config={"callbacks": [tracer]})

        tool_calls: list[ToolCall] = []
        if hasattr(response, "tool_calls") and response.tool_calls:
            for tc in response.tool_calls:
                tool_calls.append(
                    ToolCall(
                        id=tc.get("id", ""),
                        name=tc.get("name", ""),
                        arguments=tc.get("args", {}),
                    )
                )

        usage = response.usage_metadata or {}
        content = response.content if isinstance(response.content, str) else ""

        # If content is a list (mixed tool_use blocks), extract text parts
        if isinstance(response.content, list):
            text_parts = [
                block.get("text", "") if isinstance(block, dict) else str(block)
                for block in response.content
                if not isinstance(block, dict) or block.get("type") != "tool_use"
            ]
            content = " ".join(text_parts).strip()

        stop_reason = "tool_use" if tool_calls else "end_turn"

        return LLMResponse(
            content=content,
            tool_calls=tool_calls,
            input_tokens=usage.get("input_tokens", 0),
            output_tokens=usage.get("output_tokens", 0),
            stop_reason=stop_reason,
        )
