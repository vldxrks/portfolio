from abc import ABC, abstractmethod
from dataclasses import dataclass


class AIProviderError(Exception):
    """Temporary or permanent provider failure (network, quota, bad key...)."""


@dataclass
class Usage:
    model: str = ""
    input_tokens: int = 0
    output_tokens: int = 0


class AIProvider(ABC):
    """Business logic depends on this interface only, never on a concrete SDK."""

    name = "base"

    @abstractmethod
    def analyze_resume(self, text: str) -> tuple[str, Usage]:
        """Return (raw JSON string, usage). Validation happens in the service layer."""
