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

logger = logging.getLogger(__name__)

# Provider singleton cache for connection reuse
_provider_cache: dict = {}


def get_provider(provider_name: Optional[str] = None) -> BaseProvider:
    """
    Get an AI provider instance based on settings.
    Providers are cached until settings change.
    
    Args:
        provider_name: Override the active provider from settings.
    
    Returns:
        An instance of BaseProvider.
    
    Raises:
        ValueError: If provider is not configured or enabled.
    """
    settings = config_manager.settings
    name = provider_name or settings.active_provider
    
    cache_key = f"{name}_{settings.ollama.base_url if name == 'ollama' else getattr(getattr(settings, name, None), 'api_key', '')}"
    
    if cache_key in _provider_cache:
        return _provider_cache[cache_key]
    
    if name == "ollama":
        provider = OllamaProvider(base_url=settings.ollama.base_url)
    elif name == "openai":
        cfg = settings.openai
        if not cfg.api_key:
            raise ValueError("OpenAI API key not configured. Go to Settings > AI Providers.")
        provider = OpenAIProvider(api_key=cfg.api_key, default_model=cfg.default_model or "gpt-4o-mini")
    elif name == "gemini":
        cfg = settings.gemini
        if not cfg.api_key:
            raise ValueError("Gemini API key not configured. Go to Settings > AI Providers.")
        provider = GeminiProvider(api_key=cfg.api_key, default_model=cfg.default_model or "gemini-2.5-flash")
    elif name == "anthropic":
        cfg = settings.anthropic
        if not cfg.api_key:
            raise ValueError("Anthropic API key not configured. Go to Settings > AI Providers.")
        provider = AnthropicProvider(api_key=cfg.api_key, default_model=cfg.default_model or "claude-sonnet-4-20250514")
    elif name == "openrouter":
        cfg = settings.openrouter
        if not cfg.api_key:
            raise ValueError("OpenRouter API key not configured. Go to Settings > AI Providers.")
        provider = OpenRouterProvider(
            api_key=cfg.api_key,
            base_url=cfg.base_url or "https://openrouter.ai/api/v1",
            default_model=cfg.default_model or "meta-llama/llama-3.3-70b-instruct",
        )
    else:
        raise ValueError(f"Unknown provider: {name}")
    
    _provider_cache[cache_key] = provider
    return provider


def clear_provider_cache():
    """Clear the provider cache. Call after settings changes."""
    _provider_cache.clear()


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
    
    template = prompt_obj.prompt_template
    template = template.replace("{content}", content)
    template = template.replace("{target_lang}", resolved_lang)
    template = template.replace("{user_prompt}", user_prompt or "")
    return template


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
