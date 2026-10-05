from django.conf import settings

from .base import AIProvider, AIProviderError, Usage  # noqa: F401


def get_provider() -> AIProvider:
    """Factory: provider is chosen by env config, never by the user."""
    name = settings.AI_PROVIDER.lower()
    if name == "openai":
        from .openai_provider import OpenAIProvider

        return OpenAIProvider()
    if name in {"local", "fake"}:
        from .local_provider import LocalHeuristicProvider

        return LocalHeuristicProvider()
    raise AIProviderError(f"Unknown AI_PROVIDER: {name}")
