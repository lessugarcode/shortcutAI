"""
shortcutAI — Google Gemini Provider
BYOK support for Google Gemini API.
"""

import asyncio
import base64
from typing import AsyncGenerator, Optional
from google import genai
from google.genai import types

from .base import BaseProvider, AIMessage, AIResponse


RETRYABLE_CODES = {429, 500, 502, 503, 504}


def _is_retryable(error: Exception) -> bool:
    code = getattr(error, 'code', None) or getattr(error, 'status_code', None)
    if code in RETRYABLE_CODES:
        return True
    msg = str(error).lower()
    return any(k in msg for k in ('unavailable', 'overloaded', 'rate', 'timeout', 'capacity'))


async def _retry_with_backoff(fn, max_retries: int = 2):
    last_error = None
    for attempt in range(max_retries + 1):
        try:
            return await fn()
        except Exception as e:
            last_error = e
            if attempt < max_retries and _is_retryable(e):
                delay = (attempt + 1) * 2
                await asyncio.sleep(delay)
                continue
            raise
    raise last_error  # type: ignore


class GeminiProvider(BaseProvider):
    """Provider for Google Gemini API (BYOK)."""
    
    name = "gemini"
    supports_vision = True
    supports_streaming = True
    
    def __init__(self, api_key: str, default_model: str = "gemini-2.5-flash"):
        self.api_key = api_key
        self.default_model = default_model
        self.client = genai.Client(api_key=api_key)
    
    async def generate(
        self,
        messages: list[AIMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 8192,
    ) -> AIResponse:
        model = model or self.default_model
        contents = self._format_messages(messages)
        
        response = await _retry_with_backoff(
            lambda: self.client.aio.models.generate_content(
                model=model,
                contents=contents,
                config=types.GenerateContentConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                ),
            )
        )
        
        return AIResponse(
            text=response.text or "",
            model=model,
            provider=self.name,
            usage={
                "prompt_tokens": response.usage_metadata.prompt_token_count if response.usage_metadata else 0,
                "completion_tokens": response.usage_metadata.candidates_token_count if response.usage_metadata else 0,
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
        contents = self._format_messages(messages)
        
        response_stream = await _retry_with_backoff(
            lambda: self.client.aio.models.generate_content_stream(
                model=model,
                contents=contents,
                config=types.GenerateContentConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                ),
            )
        )
        
        async for chunk in response_stream:
            if chunk.text:
                yield chunk.text
    
    async def list_models(self) -> list[str]:
        try:
            models = []
            response = await self.client.aio.models.list()
            async for model in response:
                if "gemini" in model.name.lower():
                    models.append(model.name.replace("models/", ""))
            return sorted(models)
        except Exception:
            return ["gemini-2.5-flash", "gemini-2.5-pro"]
    
    async def health_check(self) -> bool:
        try:
            response = await self.client.aio.models.list()
            async for _ in response:
                return True
            return True
        except Exception:
            return False
    
    def _format_messages(self, messages: list[AIMessage]) -> list:
        contents = []
        for msg in messages:
            parts = []
            if msg.content:
                parts.append(msg.content)
            if msg.image_base64:
                image_bytes = base64.b64decode(msg.image_base64)
                parts.append(types.Part.from_bytes(
                    data=image_bytes,
                    mime_type=msg.image_mime_type or "image/png",
                ))
            contents.append(types.Content(
                role="user" if msg.role == "user" else "model",
                parts=[types.Part.from_text(text=p) if isinstance(p, str) else p for p in parts],
            ))
        return contents
