"""
Right Click AI — Anthropic Provider
BYOK support for Anthropic Claude API.
"""

from typing import AsyncGenerator, Optional
from anthropic import AsyncAnthropic

from .base import BaseProvider, AIMessage, AIResponse


class AnthropicProvider(BaseProvider):
    """Provider for Anthropic Claude API (BYOK)."""
    
    name = "anthropic"
    supports_vision = True
    supports_streaming = True
    
    def __init__(self, api_key: str, default_model: str = "claude-sonnet-4-20250514"):
        self.api_key = api_key
        self.default_model = default_model
        self.client = AsyncAnthropic(api_key=api_key)
    
    async def generate(
        self,
        messages: list[AIMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> AIResponse:
        model = model or self.default_model
        formatted = self._format_messages(messages)
        
        response = await self.client.messages.create(
            model=model,
            messages=formatted,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        
        text = ""
        for block in response.content:
            if block.type == "text":
                text += block.text
        
        return AIResponse(
            text=text,
            model=model,
            provider=self.name,
            usage={
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens,
            }
        )
    
    async def generate_stream(
        self,
        messages: list[AIMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> AsyncGenerator[str, None]:
        model = model or self.default_model
        formatted = self._format_messages(messages)
        
        async with self.client.messages.stream(
            model=model,
            messages=formatted,
            temperature=temperature,
            max_tokens=max_tokens,
        ) as stream:
            async for text in stream.text_stream:
                yield text
    
    async def list_models(self) -> list[str]:
        return [
            "claude-sonnet-4-20250514",
            "claude-haiku-4-20250414",
            "claude-opus-4-20250918",
        ]
    
    async def health_check(self) -> bool:
        try:
            # Simple check with minimal tokens
            await self.client.messages.create(
                model=self.default_model,
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=5,
            )
            return True
        except Exception:
            return False
    
    def _format_messages(self, messages: list[AIMessage]) -> list[dict]:
        formatted = []
        for msg in messages:
            if msg.image_base64:
                content = [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": msg.image_mime_type or "image/png",
                            "data": msg.image_base64,
                        }
                    },
                    {"type": "text", "text": msg.content},
                ]
                formatted.append({"role": msg.role, "content": content})
            else:
                formatted.append({"role": msg.role, "content": msg.content})
        return formatted
