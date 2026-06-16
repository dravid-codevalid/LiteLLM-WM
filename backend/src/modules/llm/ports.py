# File: ports.py. Description: LLM integration interface. Consists of: Abstract Base Classes and dataclasses defining the LLM provider interface.
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass


@dataclass
class LLMUsage:
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


@dataclass
class LLMStreamResult:
    content: str
    usage: LLMUsage


class LLMProvider(ABC):
    @abstractmethod
    async def stream(
        self,
        model: str,
        messages: list[dict],
        api_key: str,
    ) -> AsyncIterator[str]:
        """Yields content chunks as strings."""
        ...

    @abstractmethod
    def get_usage(self) -> LLMUsage:
        """Returns token usage after stream completes."""
        ...
