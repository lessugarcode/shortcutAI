"""
Unit tests for AI action service.
Provider dependencies are pre-mocked to avoid requiring all SDKs.
"""

import sys
import os
from unittest.mock import patch, MagicMock
import pytest

# Ensure backend is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Pre-populate sys.modules to avoid importing heavy provider SDKs
sys.modules["google"] = MagicMock()
sys.modules["google.genai"] = MagicMock()
sys.modules["anthropic"] = MagicMock()
sys.modules["openai"] = MagicMock()

from services.actions import resolve_prompt, get_provider, clear_provider_cache
from config import AppSettings, CustomPrompt, OllamaConfig, ProviderConfig


# --- Fixtures ---

@pytest.fixture
def mock_settings():
    """Provide default AppSettings for testing."""
    return AppSettings(
        active_provider="ollama",
        language="id",
    )


@pytest.fixture
def mock_prompts():
    """Provide test custom prompts."""
    return [
        CustomPrompt(
            id="translate",
            name="Terjemahkan",
            icon="🌐",
            prompt_template="Translate: {content} to {target_lang}",
            description="Translate text",
            content_types=["text"],
        ),
        CustomPrompt(
            id="ask_ai",
            name="Tanya AI",
            icon="💬",
            prompt_template="{user_prompt}\n\nContext:\n{content}",
            description="Ask AI",
            content_types=["text", "code", "image"],
        ),
    ]


# --- resolve_prompt tests ---

class TestResolvePrompt:
    def test_resolve_translate(self, mock_settings, mock_prompts):
        """Test resolve_prompt for the translate action."""
        with patch("services.actions.config_manager") as mock_cm:
            mock_cm.settings = mock_settings
            mock_cm.custom_prompts = mock_prompts

            result = resolve_prompt(
                action_id="translate",
                content="Hello world",
                target_lang="id",
            )
            assert "Hello world" in result
            assert "Indonesia" in result

    def test_resolve_unknown_action(self, mock_settings, mock_prompts):
        """Test resolve_prompt raises for unknown action_id."""
        with patch("services.actions.config_manager") as mock_cm:
            mock_cm.settings = mock_settings
            mock_cm.custom_prompts = mock_prompts

            with pytest.raises(ValueError, match="Unknown action"):
                resolve_prompt(action_id="nonexistent", content="test")

    def test_resolve_ask_ai(self, mock_settings, mock_prompts):
        """Test resolve_prompt for ask_ai with user_prompt."""
        with patch("services.actions.config_manager") as mock_cm:
            mock_cm.settings = mock_settings
            mock_cm.custom_prompts = mock_prompts

            result = resolve_prompt(
                action_id="ask_ai",
                content="some context",
                user_prompt="Explain this",
            )
            assert "Explain this" in result
            assert "some context" in result

    def test_resolve_with_default_language(self, mock_settings, mock_prompts):
        """Test resolve_prompt uses default language when not specified."""
        with patch("services.actions.config_manager") as mock_cm:
            mock_cm.settings = mock_settings
            mock_cm.custom_prompts = mock_prompts

            result = resolve_prompt(
                action_id="translate",
                content="Hello",
            )
            assert "Indonesia" in result  # default lang is 'id'


# --- get_provider tests ---

class TestGetProvider:
    def test_get_provider_unknown(self, mock_settings):
        """Test get_provider raises for unknown provider name."""
        clear_provider_cache()
        with patch("services.actions.config_manager") as mock_cm:
            mock_cm.settings = mock_settings
            with pytest.raises(ValueError, match="Unknown provider"):
                get_provider(provider_name="nonexistent")

    def test_get_openai_disabled(self):
        """Test get_provider raises when OpenAI is disabled."""
        clear_provider_cache()
        settings = AppSettings(
            active_provider="ollama",
            openai=ProviderConfig(enabled=False),
        )
        with patch("services.actions.config_manager") as mock_cm:
            mock_cm.settings = settings
            with pytest.raises(ValueError, match="disabled"):
                get_provider(provider_name="openai")

    def test_get_openai_no_api_key(self):
        """Test get_provider raises when OpenAI has no API key."""
        clear_provider_cache()
        settings = AppSettings(
            active_provider="ollama",
            openai=ProviderConfig(enabled=True, api_key=None),
        )
        with patch("services.actions.config_manager") as mock_cm:
            mock_cm.settings = settings
            with pytest.raises(ValueError, match="API key"):
                get_provider(provider_name="openai")


# --- Content detection tests ---

class TestContentDetection:
    def test_detect_code_python(self):
        from services.context_detector import detect_content_type
        result = detect_content_type(
            "def hello():\n    print('world')\n    return True"
        )
        assert result == "code"

    def test_detect_code_javascript(self):
        from services.context_detector import detect_content_type
        result = detect_content_type(
            "const x = 1;\nfunction foo() {\n  return x + 2;\n}"
        )
        assert result == "code"

    def test_detect_plain_text(self):
        from services.context_detector import detect_content_type
        result = detect_content_type("Hello, this is plain text.")
        assert result == "text"

    def test_detect_image(self):
        from services.context_detector import detect_content_type
        result = detect_content_type("", has_image=True)
        assert result == "image"

    def test_detect_empty_content(self):
        from services.context_detector import detect_content_type
        result = detect_content_type("")
        assert result == "text"
