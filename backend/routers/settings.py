"""
shortcutAI — Settings Router
API endpoints for managing app settings and custom prompts.
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from config import config_manager, CustomPrompt
from utils.security import mask_api_key
from services.actions import clear_provider_cache

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/settings", tags=["Settings"])


# --- Request Models ---

class UpdateSettingsRequest(BaseModel):
    """Partial settings update."""
    hotkey: Optional[str] = None
    language: Optional[str] = None
    theme: Optional[str] = None
    active_provider: Optional[str] = None
    stream_responses: Optional[bool] = None
    auto_paste: Optional[bool] = None
    ollama: Optional[dict] = None
    openai: Optional[dict] = None
    gemini: Optional[dict] = None
    anthropic: Optional[dict] = None
    openrouter: Optional[dict] = None


class CustomPromptRequest(BaseModel):
    id: str
    name: str
    icon: str = "💬"
    prompt_template: str
    description: str = ""
    content_types: list[str] = ["text"]


# --- Endpoints ---

@router.get("")
async def get_settings() -> dict:
    """Get current app settings (API keys are masked)."""
    settings = config_manager.settings
    data = settings.model_dump()
    
    # Mask API keys for security
    for provider in ["openai", "gemini", "anthropic", "openrouter"]:
        if data.get(provider, {}).get("api_key"):
            data[provider]["api_key"] = mask_api_key(data[provider]["api_key"])
    
    return data


@router.put("")
async def update_settings(req: UpdateSettingsRequest) -> dict:
    """Update app settings (partial update)."""
    try:
        updates = req.model_dump(exclude_none=True)
        if not updates:
            return config_manager.settings.model_dump()
        
        new_settings = config_manager.update_settings(updates)
        clear_provider_cache()
        logger.info(f"Settings updated: {list(updates.keys())}")
        
        result = new_settings.model_dump()
        # Mask API keys in response
        for provider in ["openai", "gemini", "anthropic", "openrouter"]:
            if result.get(provider, {}).get("api_key"):
                result[provider]["api_key"] = mask_api_key(result[provider]["api_key"])
        
        return result
    except Exception as e:
        logger.error(f"Failed to update settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/prompts")
async def get_custom_prompts() -> list[dict]:
    """Get all custom prompts."""
    return [p.model_dump() for p in config_manager.custom_prompts]


@router.post("/prompts")
async def create_custom_prompt(req: CustomPromptRequest) -> dict:
    """Create a new custom prompt."""
    prompts = config_manager.custom_prompts
    
    # Check for duplicate ID
    if any(p.id == req.id for p in prompts):
        raise HTTPException(status_code=400, detail=f"Prompt with id '{req.id}' already exists")
    
    new_prompt = CustomPrompt(**req.model_dump())
    prompts.append(new_prompt)
    config_manager.save_custom_prompts(prompts)
    
    logger.info(f"Custom prompt created: {req.id}")
    return new_prompt.model_dump()


@router.put("/prompts/{prompt_id}")
async def update_custom_prompt(prompt_id: str, req: CustomPromptRequest) -> dict:
    """Update an existing custom prompt."""
    prompts = config_manager.custom_prompts
    
    for i, p in enumerate(prompts):
        if p.id == prompt_id:
            prompts[i] = CustomPrompt(**req.model_dump())
            config_manager.save_custom_prompts(prompts)
            logger.info(f"Custom prompt updated: {prompt_id}")
            return prompts[i].model_dump()
    
    raise HTTPException(status_code=404, detail=f"Prompt '{prompt_id}' not found")


@router.delete("/prompts/{prompt_id}")
async def delete_custom_prompt(prompt_id: str) -> dict:
    """Delete a custom prompt."""
    prompts = config_manager.custom_prompts
    
    for i, p in enumerate(prompts):
        if p.id == prompt_id:
            removed = prompts.pop(i)
            config_manager.save_custom_prompts(prompts)
            logger.info(f"Custom prompt deleted: {prompt_id}")
            return {"deleted": removed.model_dump()}
    
    raise HTTPException(status_code=404, detail=f"Prompt '{prompt_id}' not found")
