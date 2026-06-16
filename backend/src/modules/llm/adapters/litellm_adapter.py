# File: litellm_adapter.py. Description: LiteLLM concrete implementation. Consists of: LiteLLMAdapter class implementing the LLMProvider interface for streaming and token usage.
import logging
from collections.abc import AsyncIterator

import litellm
from litellm import acompletion
from litellm.utils import trim_messages

from src.modules.llm.ports import LLMProvider, LLMUsage

logger = logging.getLogger(__name__)


class LiteLLMAdapter(LLMProvider):
    def __init__(self):
        self._usage: LLMUsage | None = None

    async def stream(
        self,
        model: str,
        messages: list[dict],
        api_key: str,
    ) -> AsyncIterator[str]:
        # Trim messages to fit context window — may fail for custom models
        # not in LiteLLM's model_cost dictionary
        try:
            trimmed = trim_messages(messages, model=model)
        except Exception as e:
            logger.warning(
                f"trim_messages failed for model '{model}': {e}. "
                "Using untrimmed messages (custom/unknown model)."
            )
            trimmed = messages

        response = await acompletion(
            model=model,
            messages=trimmed,
            api_key=api_key,
            stream=True,
            stream_options={"include_usage": True},
        )

        prompt_tokens = 0
        completion_tokens = 0

        async for chunk in response:
            delta = chunk.choices[0].delta
            if delta and delta.content:
                yield delta.content

            # Capture usage from the final chunk (requires stream_options)
            if hasattr(chunk, "usage") and chunk.usage:
                prompt_tokens = chunk.usage.prompt_tokens or 0
                completion_tokens = chunk.usage.completion_tokens or 0

        self._usage = LLMUsage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
        )

    def get_usage(self) -> LLMUsage:
        if self._usage is None:
            return LLMUsage(0, 0, 0)
        return self._usage
