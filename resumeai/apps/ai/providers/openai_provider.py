from django.conf import settings

from apps.ai.prompts import build_resume_messages

from .base import AIProvider, AIProviderError, Usage


class OpenAIProvider(AIProvider):
    name = "openai"

    def __init__(self):
        if not settings.AI_API_KEY or not settings.AI_MODEL:
            raise AIProviderError("AI_API_KEY and AI_MODEL must be configured for the openai provider")
        from openai import OpenAI

        self.client = OpenAI(api_key=settings.AI_API_KEY, timeout=settings.AI_TIMEOUT, max_retries=0)
        self.model = settings.AI_MODEL

    def analyze_resume(self, text: str) -> tuple[str, Usage]:
        kwargs = {}
        if settings.AI_TEMPERATURE:  # only send parameters the chosen model supports
            kwargs["temperature"] = float(settings.AI_TEMPERATURE)
        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=build_resume_messages(text),
                response_format={"type": "json_object"},
                **kwargs,
            )
        except Exception as exc:  # SDK raises many error types; never leak details/keys to users
            raise AIProviderError(type(exc).__name__) from exc
        usage = resp.usage
        return resp.choices[0].message.content or "", Usage(
            model=self.model,
            input_tokens=getattr(usage, "prompt_tokens", 0) or 0,
            output_tokens=getattr(usage, "completion_tokens", 0) or 0,
        )
