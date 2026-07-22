"""
shortcutAI — Security Utilities
Handles API key encryption and secure storage.

Uses OS-native credential storage via keyring when available:
- Windows: Credential Manager
- macOS: Keychain
- Linux: Secret Service / KWallet

Falls back to Fernet encryption stored in ~/.rightclick-ai/ if keyring
is not installed or fails.
"""

import os
import base64
import json
import logging
from pathlib import Path
from cryptography.fernet import Fernet

logger = logging.getLogger("rightclick-ai.security")

_APP_DATA_DIR = Path(os.environ.get(
    "RIGHTCLICK_AI_DATA",
    Path.home() / ".rightclick-ai"
))
_APP_DATA_DIR.mkdir(parents=True, exist_ok=True)

KEY_FILE = _APP_DATA_DIR / ".encryption_key"
_FALLBACK_STORE = _APP_DATA_DIR / "keys.json"  # Fernet fallback key store
_KEYRING_SERVICE = "rightclick-ai"


def _read_fallback_store() -> dict:
    """Read the fallback key store file."""
    if not _FALLBACK_STORE.exists():
        return {}
    try:
        return json.loads(_FALLBACK_STORE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _write_fallback_store(data: dict) -> None:
    """Write the fallback key store file."""
    _FALLBACK_STORE.write_text(json.dumps(data), encoding="utf-8")
    # Set file as hidden on Windows
    try:
        import ctypes
        ctypes.windll.kernel32.SetFileAttributesW(
            str(_FALLBACK_STORE), 0x02  # FILE_ATTRIBUTE_HIDDEN
        )
    except Exception:
        pass


def _write_fallback_key(provider_name: str, encoded_key: str) -> None:
    """Persist a Fernet-encrypted key to the fallback store."""
    store = _read_fallback_store()
    store[provider_name] = encoded_key
    _write_fallback_store(store)


def _read_fallback_key(provider_name: str) -> str | None:
    """Read a Fernet-encrypted key from the fallback store."""
    store = _read_fallback_store()
    return store.get(provider_name)

# --- Keyring availability check ---
_keyring_available = False
try:
    import keyring
    # Quick smoke test: can we get the backend?
    _backend = keyring.get_keyring()
    _keyring_available = True
    logger.info("keyring available — using OS-native credential storage")
except Exception:
    logger.info("keyring not available — falling back to Fernet file storage")


def _get_or_create_key() -> bytes:
    """Get or create an encryption key for API key storage."""
    if KEY_FILE.exists():
        return KEY_FILE.read_bytes()
    
    key = Fernet.generate_key()
    KEY_FILE.write_bytes(key)
    
    # Set file as hidden on Windows
    try:
        import ctypes
        ctypes.windll.kernel32.SetFileAttributesW(str(KEY_FILE), 0x02)  # FILE_ATTRIBUTE_HIDDEN
    except Exception:
        pass
    
    return key


def encrypt_api_key(provider_name: str, api_key: str) -> None:
    """
    Securely store an API key for a provider.

    Prefers OS-native credential storage (Windows Credential Manager,
    macOS Keychain, etc.) via keyring. Falls back to Fernet-encrypted
    file storage if keyring is unavailable.
    """
    if _keyring_available:
        try:
            keyring.set_password(_KEYRING_SERVICE, provider_name, api_key)
            logger.debug("Stored API key for %s via keyring", provider_name)
            return
        except Exception as exc:
            logger.warning("keyring.set_password failed for %s: %s — falling back to Fernet",
                           provider_name, exc)

    # Fallback: Fernet-encrypted file storage
    key = _get_or_create_key()
    f = Fernet(key)
    encrypted = f.encrypt(api_key.encode())
    encoded = base64.urlsafe_b64encode(encrypted).decode()
    _write_fallback_key(provider_name, encoded)


def decrypt_api_key(provider_name: str) -> str | None:
    """
    Retrieve a stored API key for a provider.

    Prefers OS-native credential storage via keyring.
    Falls back to Fernet-encrypted file storage.
    Returns None if no key is found.
    """
    if _keyring_available:
        try:
            result = keyring.get_password(_KEYRING_SERVICE, provider_name)
            if result is not None:
                return result
            # Keyring returned None — key not found; fall through to fallback
        except Exception as exc:
            logger.warning("keyring.get_password failed for %s: %s — falling back to Fernet",
                           provider_name, exc)

    # Fallback: Fernet-encrypted file storage
    encoded = _read_fallback_key(provider_name)
    if encoded is None:
        return None
    key = _get_or_create_key()
    f = Fernet(key)
    encrypted = base64.urlsafe_b64decode(encoded.encode())
    return f.decrypt(encrypted).decode()


def mask_api_key(api_key: str) -> str:
    """Mask an API key for display purposes."""
    if not api_key:
        return ""
    if len(api_key) <= 8:
        return "****"
    return api_key[:4] + "•" * (len(api_key) - 8) + api_key[-4:]
