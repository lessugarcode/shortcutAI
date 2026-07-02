"""
Right Click AI — Ollama Provider
Local AI model support via Ollama API.
"""

import httpx
from typing import AsyncGenerator, Optional

from .base import BaseProvider, AIMessage, AIResponse


class OllamaProvider(BaseProvider):
    """Provider for local Ollama models."""
    
    name = "ollama"
    supports_vision = True
    supports_streaming = True
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=120.0)
    
    async def generate(
        self,
        messages: list[AIMessage],
        model: Optional[str] = "llama3.2",
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> AIResponse:
        payload = self._build_payload(messages, model, temperature, max_tokens, stream=False)
        
        response = await self.client.post("/api/chat", json=payload)
        response.raise_for_status()
        data = response.json()
        
        return AIResponse(
            text=data["message"]["content"],
            model=model or "llama3.2",
            provider=self.name,
            usage={
                "prompt_tokens": data.get("prompt_eval_count", 0),
                "completion_tokens": data.get("eval_count", 0),
            }
        )
    
    async def generate_stream(
        self,
        messages: list[AIMessage],
        model: Optional[str] = "llama3.2",
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> AsyncGenerator[str, None]:
        payload = self._build_payload(messages, model, temperature, max_tokens, stream=True)
        
        async with self.client.stream("POST", "/api/chat", json=payload) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line:
                    import json
                    data = json.loads(line)
                    if "message" in data and "content" in data["message"]:
                        chunk = data["message"]["content"]
                        if chunk:
                            yield chunk
                    if data.get("done", False):
                        break
    
    async def list_models(self) -> list[str]:
        try:
            response = await self.client.get("/api/tags")
            response.raise_for_status()
            data = response.json()
            return [m["name"] for m in data.get("models", [])]
        except Exception:
            return []
    
    async def health_check(self) -> bool:
        try:
            response = await self.client.get("/api/tags")
            return response.status_code == 200
        except Exception:
            return False
    
    def _build_payload(
        self,
        messages: list[AIMessage],
        model: Optional[str],
        temperature: float,
        max_tokens: int,
        stream: bool,
    ) -> dict:
        formatted_messages = []
        for msg in messages:
            entry = {"role": msg.role, "content": msg.content}
            if msg.image_base64:
                entry["images"] = [msg.image_base64]
            formatted_messages.append(entry)
        
        return {
            "model": model or "llama3.2",
            "messages": formatted_messages,
            "stream": stream,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            }
        }
