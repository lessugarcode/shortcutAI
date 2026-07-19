"""
Unit tests for config and security modules.
"""

import sys
import os
import json
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import AppSettings, ProviderConfig, ConfigManager, APP_DATA_DIR, CONFIG_FILE
from utils.security import encrypt_api_key, decrypt_api_key, mask_api_key


class TestApiKeyEncryption:
    """Test API key encrypt/decrypt roundtrip via key storage."""

    def test_encrypt_decrypt_roundtrip(self):
        """Store and retrieve an API key."""
        provider = "test_provider_roundtrip"
        original = "sk-test-key-12345-abcdefghijklmnop"

        encrypt_api_key(provider, original)
        result = decrypt_api_key(provider)
        assert result == original

    def test_encrypt_decrypt_special_chars(self):
        """Store and retrieve keys with special characters."""
        provider = "test_provider_special"
        original = "key-with!@#$%^&*()_+={}[]|:;'<>,.?/~`"

        encrypt_api_key(provider, original)
        result = decrypt_api_key(provider)
        assert result == original

    def test_decrypt_nonexistent_key(self):
        """Retrieving a key that was never stored returns None."""
        result = decrypt_api_key("nonexistent_provider_xyz")
        assert result is None

    def test_overwrite_key(self):
        """Storing a key twice overwrites the previous value."""
        provider = "test_provider_overwrite"
        encrypt_api_key(provider, "first-key")
        encrypt_api_key(provider, "second-key")
        result = decrypt_api_key(provider)
        assert result == "second-key"


class TestMaskApiKey:
    """Test API key masking for display."""

    def test_mask_normal_key(self):
        result = mask_api_key("sk-abcdefghijklmnop1234567890")
        assert result.startswith("sk-a")
        assert result.endswith("7890")
        assert "•" in result

    def test_mask_short_key(self):
        result = mask_api_key("short")
        assert result == "****"

    def test_mask_empty_key(self):
        result = mask_api_key("")
        assert result == ""

    def test_mask_none_key(self):
        result = mask_api_key(None)
        assert result == ""


class TestAppSettings:
    """Test AppSettings model defaults and serialization."""

    def test_default_settings(self):
        settings = AppSettings()
        assert settings.active_provider == "ollama"
        assert settings.language == "id"
        assert settings.hotkey == "CommandOrControl+Shift+Q"
        assert settings.stream_responses is True

    def test_custom_settings(self):
        settings = AppSettings(
            active_provider="openai",
            language="en",
            openai=ProviderConfig(enabled=True, api_key="test-key"),
        )
        assert settings.active_provider == "openai"
        assert settings.openai.enabled is True
        assert settings.openai.api_key == "test-key"

    def test_model_dump_and_restore(self):
        """Settings should survive JSON roundtrip."""
        settings = AppSettings(
            active_provider="gemini",
            language="ja",
            gemini=ProviderConfig(enabled=True, api_key="some-key"),
        )
        dumped = settings.model_dump()
        restored = AppSettings(**dumped)
        assert restored.active_provider == "gemini"
        assert restored.language == "ja"
        assert restored.gemini.api_key == "some-key"
