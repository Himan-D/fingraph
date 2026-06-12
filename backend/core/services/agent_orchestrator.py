import json
import logging
from typing import Any, AsyncIterator, Dict, List, Optional

from openai import AsyncOpenAI

from config import settings
from core.services.agent_tools import SYSTEM_PROMPT, TOOL_DEFINITIONS, TOOL_EXECUTORS
from core.services.agent_memory import agent_memory
from core.services.agent_planner import AgentPlanner, detect_plan_type

logger = logging.getLogger(__name__)

MAX_TOOL_ROUNDS = 5


class AgentOrchestrator:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = "gpt-4o"
        self.planner = AgentPlanner()

    async def _execute_tool(self, name: str, arguments: Dict[str, Any]) -> str:
        executor = TOOL_EXECUTORS.get(name)
        if not executor:
            return json.dumps({"error": f"Unknown tool: {name}"})
        try:
            result = await executor(**arguments)
            return json.dumps(result, default=str)
        except Exception as e:
            logger.error(f"Tool execution error ({name}): {e}")
            return json.dumps({"error": str(e)})

    async def _build_messages(
        self,
        user_message: str,
        history: Optional[List[Dict[str, str]]] = None,
        system_context: Optional[str] = None,
        user_id: Optional[int] = None,
        symbol: Optional[str] = None,
    ) -> List[Dict[str, str]]:
        system_text = SYSTEM_PROMPT

        memory_ctx = await agent_memory.build_system_context(
            user_id=user_id, symbol=symbol
        )
        if memory_ctx:
            system_text += f"\n\nUser context:\n{memory_ctx}"

        plan_type = detect_plan_type(user_message)
        if plan_type and symbol:
            injection = self.planner.inject_plan_into_prompt(plan_type, self.planner.detect_plan(user_message))
            if injection:
                system_text += injection

        if system_context:
            system_text += f"\n\nAdditional context:\n{system_context}"

        messages = [{"role": "system", "content": system_text}]

        if history:
            messages.extend(history)

        messages.append({"role": "user", "content": user_message})
        return messages

    async def stream_chat(
        self,
        user_message: str,
        history: Optional[List[Dict[str, str]]] = None,
        system_context: Optional[str] = None,
        user_id: Optional[int] = None,
        symbol: Optional[str] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        messages = await self._build_messages(user_message, history, system_context, user_id, symbol)
        tool_calls_log = []
        tool_results_log = []

        for round_num in range(MAX_TOOL_ROUNDS):
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=TOOL_DEFINITIONS,
                tool_choice="auto",
                stream=True,
            )

            collected_content = ""
            collected_tool_calls: Dict[int, Dict[str, Any]] = {}
            finish_reason = None

            async for chunk in response:
                delta = chunk.choices[0].delta if chunk.choices else None
                if not delta:
                    continue

                if delta.content:
                    collected_content += delta.content
                    yield {
                        "type": "token",
                        "content": delta.content,
                    }

                if delta.tool_calls:
                    for tc in delta.tool_calls:
                        idx = tc.index
                        if idx not in collected_tool_calls:
                            collected_tool_calls[idx] = {
                                "id": tc.id or "",
                                "name": "",
                                "arguments": "",
                            }
                        if tc.id:
                            collected_tool_calls[idx]["id"] = tc.id
                        if tc.function:
                            if tc.function.name:
                                collected_tool_calls[idx]["name"] = (
                                    tc.function.name
                                )
                            if tc.function.arguments:
                                collected_tool_calls[idx]["arguments"] += (
                                    tc.function.arguments
                                )

                if chunk.choices and chunk.choices[0].finish_reason:
                    finish_reason = chunk.choices[0].finish_reason

            if finish_reason == "tool_calls" and collected_tool_calls:
                if collected_content:
                    messages.append(
                        {"role": "assistant", "content": collected_content}
                    )

                tool_messages = []
                assistant_tool_calls = []
                for idx in sorted(collected_tool_calls.keys()):
                    tc_data = collected_tool_calls[idx]
                    tool_name = tc_data["name"]
                    tool_args_str = tc_data["arguments"]
                    tool_call_id = tc_data["id"]

                    try:
                        tool_args = json.loads(tool_args_str)
                    except json.JSONDecodeError:
                        tool_args = {}

                    yield {
                        "type": "tool_start",
                        "tool": tool_name,
                        "args": tool_args,
                    }

                    tool_result = await self._execute_tool(tool_name, tool_args)

                    tool_calls_log.append(
                        {
                            "name": tool_name,
                            "arguments": tool_args,
                        }
                    )
                    tool_results_log.append(
                        {
                            "name": tool_name,
                            "result_preview": tool_result[:500],
                        }
                    )

                    yield {
                        "type": "tool_end",
                        "tool": tool_name,
                        "result_preview": tool_result[:500],
                    }

                    try:
                        parsed = json.loads(tool_result)
                        if isinstance(parsed, dict) and "error" not in parsed:
                            yield {
                                "type": "tool_result",
                                "tool": tool_name,
                                "args": tool_args,
                                "data": parsed,
                            }
                    except (json.JSONDecodeError, TypeError):
                        pass

                    assistant_tool_calls.append(
                        {
                            "id": tool_call_id,
                            "type": "function",
                            "function": {
                                "name": tool_name,
                                "arguments": tool_args_str,
                            },
                        }
                    )
                    tool_messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call_id,
                            "content": tool_result,
                        }
                    )

                messages.append(
                    {
                        "role": "assistant",
                        "content": collected_content or None,
                        "tool_calls": assistant_tool_calls,
                    }
                )
                messages.extend(tool_messages)
                continue

            break

        yield {
            "type": "done",
            "tool_calls": tool_calls_log,
            "tool_results": tool_results_log,
        }

    async def chat(
        self,
        user_message: str,
        history: Optional[List[Dict[str, str]]] = None,
        system_context: Optional[str] = None,
        user_id: Optional[int] = None,
        symbol: Optional[str] = None,
    ) -> Dict[str, Any]:
        full_content = ""
        tool_calls = []
        tool_results = []

        async for event in self.stream_chat(
            user_message, history, system_context, user_id, symbol
        ):
            if event["type"] == "token":
                full_content += event["content"]
            elif event["type"] == "done":
                tool_calls = event.get("tool_calls", [])
                tool_results = event.get("tool_results", [])

        return {
            "content": full_content,
            "tool_calls": tool_calls,
            "tool_results": tool_results,
        }
