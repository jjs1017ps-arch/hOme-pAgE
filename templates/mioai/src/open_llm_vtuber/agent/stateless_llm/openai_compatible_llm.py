"""Description: This file contains the implementation of the `AsyncLLM` class.
This class is responsible for handling asynchronous interaction with OpenAI API compatible
endpoints for language generation.
"""

import asyncio
from typing import AsyncIterator, List, Dict, Any
from openai import (
    AsyncStream,
    AsyncOpenAI,
    APIError,
    APIConnectionError,
    RateLimitError,
    NotGiven,
    NOT_GIVEN,
)
from openai.types.chat import ChatCompletionChunk
from openai.types.chat.chat_completion_chunk import ChoiceDeltaToolCall
from loguru import logger

from .stateless_llm_interface import StatelessLLMInterface
from ...mcpp.types import ToolCallObject


class AsyncLLM(StatelessLLMInterface):
    def __init__(
        self,
        model: str,
        base_url: str,
        llm_api_key: str = "z",
        organization_id: str = "z",
        project_id: str = "z",
        temperature: float = 1.0,
    ):
        """
        Initializes an instance of the `AsyncLLM` class.
        """
        self.base_url = base_url
        self.model = model
        self.temperature = temperature
        self.client = AsyncOpenAI(
            base_url=base_url,
            organization=organization_id,
            project=project_id,
            api_key=llm_api_key,
        )
        self.support_tools = True

        logger.info(
            f"Initialized AsyncLLM with the parameters: {self.base_url}, {self.model}"
        )

    async def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        system: str = None,
        tools: List[Dict[str, Any]] | NotGiven = NOT_GIVEN,
    ) -> AsyncIterator[str | List[ChoiceDeltaToolCall]]:
        
        max_retries = 3
        for attempt in range(max_retries):
            stream = None
            accumulated_tool_calls = {}
            in_tool_call = False

            try:
                messages_with_system = messages
                if system:
                    messages_with_system = [
                        {"role": "system", "content": system},
                        *messages,
                    ]
                
                available_tools = tools if self.support_tools else NOT_GIVEN

                stream: AsyncStream[ChatCompletionChunk] = await self.client.chat.completions.create(
                    messages=messages_with_system,
                    model=self.model,
                    stream=True,
                    temperature=self.temperature,
                    tools=available_tools,
                )

                async for chunk in stream:
                    if self.support_tools:
                        has_tool_calls = (
                            hasattr(chunk.choices[0].delta, "tool_calls")
                            and chunk.choices[0].delta.tool_calls
                        )

                        if has_tool_calls:
                            in_tool_call = True
                            for tool_call in chunk.choices[0].delta.tool_calls:
                                index = tool_call.index if hasattr(tool_call, "index") else 0
                                if index not in accumulated_tool_calls:
                                    accumulated_tool_calls[index] = {
                                        "index": index,
                                        "id": getattr(tool_call, "id", None),
                                        "type": getattr(tool_call, "type", None),
                                        "function": {"name": "", "arguments": ""},
                                    }
                                if hasattr(tool_call, "id") and tool_call.id:
                                    accumulated_tool_calls[index]["id"] = tool_call.id
                                if hasattr(tool_call, "type") and tool_call.type:
                                    accumulated_tool_calls[index]["type"] = tool_call.type
                                if hasattr(tool_call, "function"):
                                    if hasattr(tool_call.function, "name") and tool_call.function.name:
                                        accumulated_tool_calls[index]["function"]["name"] = tool_call.function.name
                                    if hasattr(tool_call.function, "arguments") and tool_call.function.arguments:
                                        accumulated_tool_calls[index]["function"]["arguments"] += tool_call.function.arguments
                            continue
                        elif in_tool_call and not has_tool_calls:
                            in_tool_call = False
                            complete_tool_calls = [
                                ToolCallObject.from_dict(tool_data)
                                for tool_data in accumulated_tool_calls.values()
                            ]
                            yield complete_tool_calls
                            accumulated_tool_calls = {}

                    if len(chunk.choices) == 0: continue
                    content = chunk.choices[0].delta.content
                    if content is None: content = ""
                    yield content

                if in_tool_call and accumulated_tool_calls:
                    complete_tool_calls = [
                        ToolCallObject.from_dict(tool_data)
                        for tool_data in accumulated_tool_calls.values()
                    ]
                    yield complete_tool_calls
                
                # If we reached here, success! Break the retry loop.
                return

            except RateLimitError as e:
                wait_time = (attempt + 1) * 5
                logger.warning(f"⚠️ Gemini Rate Limit hit. Retrying in {wait_time}s... (Attempt {attempt+1}/{max_retries})")
                if attempt < max_retries - 1:
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    logger.error("Max retries reached for Gemini Rate Limit.")
                    yield "Error: Gemini API 차단이 풀리지 않습니다. 1분 후 다시 시도해 주세요."
                    return

            except APIConnectionError as e:
                logger.error(f"LLM API Connection error: {e}")
                yield "Error calling the chat endpoint: Connection error."
                return

            except APIError as e:
                if "does not support tools" in str(e):
                    self.support_tools = False
                    logger.warning(f"{self.model} does not support tools.")
                    yield "__API_NOT_SUPPORT_TOOLS__"
                    return
                logger.error(f"LLM API Error: {e}")
                yield "Error calling the chat endpoint: Error occurred while generating response."
                return

            finally:
                if stream:
                    await stream.close()
