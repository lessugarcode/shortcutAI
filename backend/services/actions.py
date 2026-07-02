"""
Right Click AI — AI Action Service
Orchestrates AI actions: resolves prompts, selects providers, and executes.
"""

import logging
from typing import AsyncGenerator, Optional

from config import config_manager, CustomPrompt
from providers.base import BaseProvider, AIMessage
from providers.ollama import OllamaProvider
from providers.openai_provider import OpenAIProvider
from providers.gemini import GeminiProvider
from providers.anthropic_provider import AnthropicProvider
from providers.openrouter import OpenRouterProvider
from services.context_detector import detect_content_type

logger = logging.getLogger(__name__)


def get_provider(provider_name: Optional[str] = None) -> BaseProvider:
    """
    Get an AI provider instance based on settings.
    
    Args:
        provider_name: Override the active provider from settings.
    
    Returns:
        An instance of BaseProvider.
    
    Raises:
        ValueError: If provider is not configured or enabled.
    """
    settings = config_manager.settings
    name = provider_name or settings.active_provider
    
    if name == "ollama":
        return OllamaProvider(base_url=settings.ollama.base_url)
    
    elif name == "openai":
        cfg = settings.openai
        if not cfg.api_key:
            raise ValueError("OpenAI API key not configured. Go to Settings > AI Providers.")
        return OpenAIProvider(api_key=cfg.api_key, default_model=cfg.default_model or "gpt-4o-mini")
    
    elif name == "gemini":
        cfg = settings.gemini
        if not cfg.api_key:
            raise ValueError("Gemini API key not configured. Go to Settings > AI Providers.")
        return GeminiProvider(api_key=cfg.api_key, default_model=cfg.default_model or "gemini-2.5-flash")
    
    elif name == "anthropic":
        cfg = settings.anthropic
        if not cfg.api_key:
            raise ValueError("Anthropic API key not configured. Go to Settings > AI Providers.")
        return AnthropicProvider(api_key=cfg.api_key, default_model=cfg.default_model or "claude-sonnet-4-20250514")
    
    elif name == "openrouter":
        cfg = settings.openrouter
        if not cfg.api_key:
            raise ValueError("OpenRouter API key not configured. Go to Settings > AI Providers.")
        return OpenRouterProvider(
            api_key=cfg.api_key,
            base_url=cfg.base_url or "https://openrouter.ai/api/v1",
            default_model=cfg.default_model or "meta-llama/llama-3.3-70b-instruct",
        )
    
    else:
        raise ValueError(f"Unknown provider: {name}")


def resolve_prompt(
    action_id: str,
    content: str,
    target_lang: Optional[str] = None,
    user_prompt: Optional[str] = None,
) -> str:
    """
    Resolve the prompt template for an action.
    
    Args:
        action_id: The ID of the custom prompt / action.
        content: The user's selected content.
        target_lang: Target language for translation.
        user_prompt: User's custom prompt (for 'ask_ai' action).
    
    Returns:
        The resolved prompt string.
    """
    settings = config_manager.settings
    prompts = config_manager.custom_prompts
    
    prompt_obj: Optional[CustomPrompt] = None
    for p in prompts:
        if p.id == action_id:
            prompt_obj = p
            break
    
    if not prompt_obj:
        raise ValueError(f"Unknown action: {action_id}")
    
    # Map language codes to names
    lang_map = {
        "id": "Indonesia",
        "en": "Inggris (English)",
        "ja": "Jepang (Japanese)",
        "ko": "Korea (Korean)",
        "zh": "Mandarin (Chinese)",
        "ar": "Arab (Arabic)",
        "es": "Spanyol (Spanish)",
        "fr": "Prancis (French)",
        "de": "Jerman (German)",
        "pt": "Portugis (Portuguese)",
        "ru": "Rusia (Russian)",
        "th": "Thailand (Thai)",
        "vi": "Vietnam (Vietnamese)",
        "ms": "Melayu (Malay)",
    }
    
    resolved_lang = lang_map.get(target_lang or settings.language, target_lang or settings.language)
    
    return prompt_obj.prompt_template.format(
        content=content,
        target_lang=resolved_lang,
        user_prompt=user_prompt or "",
    )


async def execute_action(
    action_id: str,
    content: str,
    image_base64: Optional[str] = None,
    image_mime_type: Optional[str] = None,
    target_lang: Optional[str] = None,
    user_prompt: Optional[str] = None,
    provider_name: Optional[str] = None,
    model: Optional[str] = None,
) -> str:
    """Execute an AI action and return the full response."""
    provider = get_provider(provider_name)
    prompt = resolve_prompt(action_id, content, target_lang, user_prompt)
    
    message = AIMessage(
        role="user",
        content=prompt,
        image_base64=image_base64,
        image_mime_type=image_mime_type,
    )
    
    response = await provider.generate(messages=[message], model=model)
    return response.text


async def execute_action_stream(
    action_id: str,
    content: str,
    image_base64: Optional[str] = None,
    image_mime_type: Optional[str] = None,
    target_lang: Optional[str] = None,
    user_prompt: Optional[str] = None,
    provider_name: Optional[str] = None,
    model: Optional[str] = None,
) -> AsyncGenerator[str, None]:
    """Execute an AI action and stream the response."""
    provider = get_provider(provider_name)
    prompt = resolve_prompt(action_id, content, target_lang, user_prompt)
    
    message = AIMessage(
        role="user",
        content=prompt,
        image_base64=image_base64,
        image_mime_type=image_mime_type,
    )
    
    async for chunk in provider.generate_stream(messages=[message], model=model):
        yield chunk
