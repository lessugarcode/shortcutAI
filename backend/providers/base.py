"""
Right Click AI — Base AI Provider
Abstract base class for all AI providers.
"""

from abc import ABC, abstractmethod
from typing import AsyncGenerator, Optional
from pydantic import BaseModel


class AIMessage(BaseModel):
    role: str = "user"
    content: str
    image_base64: Optional[str] = None
    image_mime_type: Optional[str] = None


class AIResponse(BaseModel):
    text: str
    model: str
    provider: str
    usage: Optional[dict] = None


class BaseProvider(ABC):
    """Abstract base class for AI providers."""
    
    name: str = "base"
    supports_vision: bool = False
    supports_streaming: bool = True
    
    @abstractmethod
    async def generate(
        self,
        messages: list[AIMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> AIResponse:
        """Generate a response from the AI model."""
        ...
    
    @abstractmethod
    async def generate_stream(
        self,
        messages: list[AIMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> AsyncGenerator[str, None]:
        """Stream a response from the AI model, yielding text chunks."""
        ...
    
    @abstractmethod
    async def list_models(self) -> list[str]:
        """List available models for this provider."""
        ...
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the provider is accessible."""
        ...
