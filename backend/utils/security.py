"""
Right Click AI — Security Utilities
Handles API key encryption and secure storage.
"""

import os
import base64
from pathlib import Path
from cryptography.fernet import Fernet

_APP_DATA_DIR = Path(os.environ.get(
    "RIGHTCLICK_AI_DATA",
    Path.home() / ".rightclick-ai"
))
_APP_DATA_DIR.mkdir(parents=True, exist_ok=True)

KEY_FILE = _APP_DATA_DIR / ".encryption_key"


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


def encrypt_api_key(api_key: str) -> str:
    """Encrypt an API key for secure storage."""
    key = _get_or_create_key()
    f = Fernet(key)
    encrypted = f.encrypt(api_key.encode())
    return base64.urlsafe_b64encode(encrypted).decode()


def decrypt_api_key(encrypted_key: str) -> str:
    """Decrypt a stored API key."""
    key = _get_or_create_key()
    f = Fernet(key)
    encrypted = base64.urlsafe_b64decode(encrypted_key.encode())
    return f.decrypt(encrypted).decode()


def mask_api_key(api_key: str) -> str:
    """Mask an API key for display purposes."""
    if not api_key:
        return ""
    if len(api_key) <= 8:
        return "****"
    return api_key[:4] + "•" * (len(api_key) - 8) + api_key[-4:]
