"""
Right Click AI — AI Router
API endpoints for AI actions.
"""

import json
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from services.actions import execute_action, execute_action_stream, get_provider
from services.context_detector import detect_content_type
from config import config_manager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/ai", tags=["AI"])


# --- Request/Response Models ---

class ActionRequest(BaseModel):
    action_id: str
    content: str = ""
    image_base64: Optional[str] = None
    image_mime_type: Optional[str] = None
    target_lang: Optional[str] = None
    user_prompt: Optional[str] = None
    provider: Optional[str] = None
    model: Optional[str] = None
    stream: bool = True


class ActionResponse(BaseModel):
    text: str
    action_id: str
    provider: str
    model: str


class DetectRequest(BaseModel):
    content: str = ""
    has_image: bool = False


class DetectResponse(BaseModel):
    content_type: str
    available_actions: list[dict]


class ProviderStatus(BaseModel):
    name: str
    enabled: bool
    healthy: bool
    models: list[str]


# --- Endpoints ---

@router.post("/detect")
async def detect_content(req: DetectRequest) -> DetectResponse:
    """Detect content type and return available actions."""
    content_type = detect_content_type(req.content, req.has_image)
    
    actions = []
    for prompt in config_manager.custom_prompts:
        if content_type in prompt.content_types:
            actions.append({
                "id": prompt.id,
                "name": prompt.name,
                "icon": prompt.icon,
                "description": prompt.description,
            })
    
    return DetectResponse(
        content_type=content_type,
        available_actions=actions,
    )


@router.post("/action")
async def run_action(req: ActionRequest):
    """Execute an AI action. Returns streaming SSE or JSON."""
    try:
        if req.stream:
            async def event_generator():
                try:
                    async for chunk in execute_action_stream(
                        action_id=req.action_id,
                        content=req.content,
                        image_base64=req.image_base64,
                        image_mime_type=req.image_mime_type,
                        target_lang=req.target_lang,
                        user_prompt=req.user_prompt,
                        provider_name=req.provider,
                        model=req.model,
                    ):
                        yield f"data: {json.dumps({'chunk': chunk})}\n\n"
                    yield f"data: {json.dumps({'done': True})}\n\n"
                except Exception as e:
                    logger.error(f"Streaming error: {e}")
                    yield f"data: {json.dumps({'error': str(e)})}\n\n"
            
            return StreamingResponse(
                event_generator(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no",
                },
            )
        else:
            text = await execute_action(
                action_id=req.action_id,
                content=req.content,
                image_base64=req.image_base64,
                image_mime_type=req.image_mime_type,
                target_lang=req.target_lang,
                user_prompt=req.user_prompt,
                provider_name=req.provider,
                model=req.model,
            )
            settings = config_manager.settings
            return ActionResponse(
                text=text,
                action_id=req.action_id,
                provider=req.provider or settings.active_provider,
                model=req.model or "default",
            )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Action error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/providers")
async def list_providers() -> list[ProviderStatus]:
    """List all providers and their status."""
    settings = config_manager.settings
    results = []
    
    provider_configs = [
        ("ollama", settings.ollama.enabled),
        ("openai", settings.openai.enabled),
        ("gemini", settings.gemini.enabled),
        ("anthropic", settings.anthropic.enabled),
        ("openrouter", settings.openrouter.enabled),
    ]
    
    for name, enabled in provider_configs:
        healthy = False
        models = []
        
        if enabled:
            try:
                provider = get_provider(name)
                healthy = await provider.health_check()
                if healthy:
                    models = await provider.list_models()
            except Exception:
                pass
        
        results.append(ProviderStatus(
            name=name,
            enabled=enabled if name != "ollama" else settings.ollama.enabled,
            healthy=healthy,
            models=models[:20],
        ))
    
    return results
