"""
shortcutAI — OpenRouter Provider
BYOK support for OpenRouter (access to hundreds of models with one API key).
Uses OpenAI-compatible API format.
"""

from typing import AsyncGenerator, Optional
from openai import AsyncOpenAI

from .base import BaseProvider, AIMessage, AIResponse


class OpenRouterProvider(BaseProvider):
    """Provider for OpenRouter API (BYOK). OpenAI-compatible."""
    
    name = "openrouter"
    supports_vision = True
    supports_streaming = True
    
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://openrouter.ai/api/v1",
        default_model: str = "meta-llama/llama-3.3-70b-instruct",
    ):
        self.api_key = api_key
        self.default_model = default_model
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
            default_headers={
                "HTTP-Referer": "https://rightclick-ai.app",
                "X-Title": "shortcutAI",
            }
        )
    
    async def generate(
        self,
        messages: list[AIMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 8192,
    ) -> AIResponse:
        model = model or self.default_model
        formatted = self._format_messages(messages)
        
        response = await self.client.chat.completions.create(
            model=model,
            messages=formatted,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        
        return AIResponse(
            text=response.choices[0].message.content or "",
            model=model,
            provider=self.name,
            usage={
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
            }
        )
    
    async def generate_stream(
        self,
        messages: list[AIMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 8192,
    ) -> AsyncGenerator[str, None]:
        model = model or self.default_model
        formatted = self._format_messages(messages)
        
        stream = await self.client.chat.completions.create(
            model=model,
            messages=formatted,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )
        
        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    
    async def list_models(self) -> list[str]:
        try:
            models = await self.client.models.list()
            return sorted([m.id for m in models.data][:50])  # Limit to 50
        except Exception:
            return [
                "meta-llama/llama-3.3-70b-instruct",
                "google/gemini-2.5-flash",
                "anthropic/claude-sonnet-4",
                "openai/gpt-4o-mini",
            ]
    
    async def health_check(self) -> bool:
        try:
            await self.client.models.list()
            return True
        except Exception:
            return False
    
    def _format_messages(self, messages: list[AIMessage]) -> list[dict]:
        formatted = []
        for msg in messages:
            if msg.image_base64:
                content = [
                    {"type": "text", "text": msg.content},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{msg.image_mime_type or 'image/png'};base64,{msg.image_base64}"
                        }
                    }
                ]
                formatted.append({"role": msg.role, "content": content})
            else:
                formatted.append({"role": msg.role, "content": msg.content})
        return formatted
