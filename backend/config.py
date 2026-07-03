"""
Right Click AI — Configuration Management
Handles loading/saving settings, API keys, and custom prompts.
"""

import json
import os
import logging
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field
from utils.security import encrypt_api_key, decrypt_api_key

logger = logging.getLogger(__name__)


# --- Paths ---
APP_DATA_DIR = Path(os.environ.get(
    "RIGHTCLICK_AI_DATA",
    Path.home() / ".rightclick-ai"
))
APP_DATA_DIR.mkdir(parents=True, exist_ok=True)

CONFIG_FILE = APP_DATA_DIR / "config.json"
CUSTOM_PROMPTS_FILE = APP_DATA_DIR / "custom_prompts.json"


# --- Models ---
class ProviderConfig(BaseModel):
    enabled: bool = False
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    default_model: Optional[str] = None


class OllamaConfig(BaseModel):
    enabled: bool = True
    base_url: str = "http://localhost:11434"
    default_model: str = "llama3.2"


class AppSettings(BaseModel):
    # General
    hotkey: str = "CommandOrControl+Shift+Q"
    language: str = "id"  # Default target language
    theme: str = "dark"
    
    # AI Providers
    ollama: OllamaConfig = Field(default_factory=OllamaConfig)
    openai: ProviderConfig = Field(default_factory=lambda: ProviderConfig(
        default_model="gpt-4o-mini"
    ))
    gemini: ProviderConfig = Field(default_factory=lambda: ProviderConfig(
        default_model="gemini-2.5-flash"
    ))
    anthropic: ProviderConfig = Field(default_factory=lambda: ProviderConfig(
        default_model="claude-sonnet-4-20250514"
    ))
    openrouter: ProviderConfig = Field(default_factory=lambda: ProviderConfig(
        base_url="https://openrouter.ai/api/v1",
        default_model="meta-llama/llama-3.3-70b-instruct"
    ))
    
    # Active provider
    active_provider: str = "openrouter"
    
    # Streaming
    stream_responses: bool = True


class CustomPrompt(BaseModel):
    id: str
    name: str
    icon: str = "💬"
    prompt_template: str
    description: str = ""
    content_types: list[str] = Field(default_factory=lambda: ["text"])


# --- Config Manager ---
class ConfigManager:
    """Manages application configuration persistence."""
    
    def __init__(self):
        self._settings: Optional[AppSettings] = None
        self._custom_prompts: Optional[list[CustomPrompt]] = None
    
    @property
    def settings(self) -> AppSettings:
        if self._settings is None:
            self._settings = self._load_settings()
        return self._settings
    
    @property
    def custom_prompts(self) -> list[CustomPrompt]:
        if self._custom_prompts is None:
            self._custom_prompts = self._load_custom_prompts()
        return self._custom_prompts
    
    def _load_settings(self) -> AppSettings:
        if CONFIG_FILE.exists():
            try:
                data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
                # Decrypt API keys on load; plaintext keys survive migration
                for provider in ["openai", "gemini", "anthropic", "openrouter"]:
                    if data.get(provider, {}).get("api_key"):
                        try:
                            data[provider]["api_key"] = decrypt_api_key(data[provider]["api_key"])
                        except Exception:
                            pass  # Already plaintext, will be encrypted on next save
                return AppSettings(**data)
            except Exception as e:
                logger.warning(f"Failed to load settings: {e}")
        return AppSettings()
    
    def save_settings(self, settings: AppSettings) -> None:
        self._settings = settings
        data = settings.model_dump()
        # Encrypt API keys before saving
        for provider in ["openai", "gemini", "anthropic", "openrouter"]:
            if data.get(provider, {}).get("api_key"):
                data[provider]["api_key"] = encrypt_api_key(data[provider]["api_key"])
        CONFIG_FILE.write_text(
            json.dumps(data, indent=2),
            encoding="utf-8"
        )
    
    def update_settings(self, updates: dict) -> AppSettings:
        current = self.settings.model_dump()
        self._deep_update(current, updates)
        new_settings = AppSettings(**current)
        self.save_settings(new_settings)
        return new_settings
    
    def _deep_update(self, base: dict, updates: dict) -> None:
        for key, value in updates.items():
            if isinstance(value, dict) and key in base and isinstance(base[key], dict):
                self._deep_update(base[key], value)
            else:
                base[key] = value
    
    def _load_custom_prompts(self) -> list[CustomPrompt]:
        if CUSTOM_PROMPTS_FILE.exists():
            try:
                data = json.loads(CUSTOM_PROMPTS_FILE.read_text(encoding="utf-8"))
                return [CustomPrompt(**p) for p in data]
            except Exception as e:
                logger.warning(f"Failed to load custom prompts: {e}")
        return self._default_custom_prompts()
    
    def save_custom_prompts(self, prompts: list[CustomPrompt]) -> None:
        self._custom_prompts = prompts
        CUSTOM_PROMPTS_FILE.write_text(
            json.dumps([p.model_dump() for p in prompts], indent=2),
            encoding="utf-8"
        )
    
    def _default_custom_prompts(self) -> list[CustomPrompt]:
        defaults = [
            CustomPrompt(
                id="translate",
                name="Terjemahkan",
                icon="🌐",
                prompt_template="Terjemahkan teks berikut ke bahasa {target_lang}. Berikan HANYA hasil terjemahan, tanpa penjelasan tambahan.\n\nTeks:\n{content}",
                description="Terjemahkan teks ke bahasa lain",
                content_types=["text"]
            ),
            CustomPrompt(
                id="explain",
                name="Jelaskan",
                icon="📖",
                prompt_template="Jelaskan teks berikut dengan bahasa yang sederhana dan mudah dipahami, seperti menjelaskan ke anak berusia 10 tahun. Gunakan bahasa Indonesia.\n\nTeks:\n{content}",
                description="Jelaskan teks dengan sederhana",
                content_types=["text"]
            ),
            CustomPrompt(
                id="summarize",
                name="Ringkas",
                icon="📝",
                prompt_template="Buat ringkasan singkat dan padat dari teks berikut dalam bahasa Indonesia. Fokus pada poin-poin utama.\n\nTeks:\n{content}",
                description="Buat ringkasan singkat",
                content_types=["text"]
            ),
            CustomPrompt(
                id="fix_writing",
                name="Perbaiki Tulisan",
                icon="✍️",
                prompt_template="Perbaiki tata bahasa, ejaan, dan gaya penulisan dari teks berikut agar lebih profesional dan rapi. Berikan HANYA hasil perbaikan.\n\nTeks:\n{content}",
                description="Perbaiki grammar & profesional-kan",
                content_types=["text"]
            ),
            CustomPrompt(
                id="explain_code",
                name="Jelaskan Kode",
                icon="🐛",
                prompt_template="Jelaskan kode berikut dengan bahasa Indonesia yang mudah dipahami. Jelaskan apa yang dilakukan setiap bagian penting.\n\nKode:\n```\n{content}\n```",
                description="Jelaskan apa yang dilakukan kode",
                content_types=["code"]
            ),
            CustomPrompt(
                id="review_code",
                name="Review Kode",
                icon="🔍",
                prompt_template="Review kode berikut. Identifikasi bug potensial, masalah keamanan, dan berikan saran perbaikan. Gunakan bahasa Indonesia.\n\nKode:\n```\n{content}\n```",
                description="Temukan bug dan saran perbaikan",
                content_types=["code"]
            ),
            CustomPrompt(
                id="describe_image",
                name="Jelaskan Gambar",
                icon="🖼️",
                prompt_template="Deskripsikan gambar ini dengan detail dalam bahasa Indonesia. Jelaskan apa yang terlihat, konteks, dan informasi penting lainnya.",
                description="Deskripsikan isi gambar",
                content_types=["image"]
            ),
            CustomPrompt(
                id="ocr",
                name="Ekstrak Teks (OCR)",
                icon="📄",
                prompt_template="Ekstrak semua teks yang terlihat dalam gambar ini. Berikan HANYA teks yang ditemukan, tanpa penjelasan tambahan. Pertahankan format asli sebisa mungkin.",
                description="Ambil teks dari gambar",
                content_types=["image"]
            ),
            CustomPrompt(
                id="ask_ai",
                name="Tanya AI",
                icon="💬",
                prompt_template="{user_prompt}\n\nKonteks:\n{content}",
                description="Tanya AI dengan prompt bebas",
                content_types=["text", "code", "image"]
            ),
        ]
        self.save_custom_prompts(defaults)
        return defaults


# Singleton
config_manager = ConfigManager()
