"""
Secure encryption/decryption for GitHub credentials.

Uses Fernet symmetric encryption (AES-128-CBC + HMAC-SHA256).
Key is derived from GITHUB_ENCRYPTION_KEY in .env.
"""

import os
import base64
from pathlib import Path

from dotenv import load_dotenv
from cryptography.fernet import Fernet

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(PROJECT_ROOT / ".env")

_raw_key = os.getenv("GITHUB_ENCRYPTION_KEY", "")

if _raw_key:
    # Accept a raw 32-byte base64url key or any string; derive a Fernet key.
    try:
        # If already a valid Fernet key (44 chars base64url), use directly.
        _fernet = Fernet(_raw_key.encode() if isinstance(_raw_key, str) else _raw_key)
    except Exception:
        # Derive a valid 32-byte key from whatever string was given.
        import hashlib
        key_bytes = hashlib.sha256(_raw_key.encode()).digest()
        _fernet = Fernet(base64.urlsafe_b64encode(key_bytes))
else:
    # Generate a temporary in-process key; warn that tokens won't survive restarts.
    import logging
    logging.getLogger("lia").warning(
        "GITHUB_ENCRYPTION_KEY not set — generating a temporary key. "
        "GitHub tokens will be invalidated on server restart. "
        "Set GITHUB_ENCRYPTION_KEY in .env for persistence."
    )
    _fernet = Fernet(Fernet.generate_key())


def encrypt_token(plaintext: str) -> str:
    """Encrypt a GitHub token for storage."""
    return _fernet.encrypt(plaintext.encode()).decode()


def decrypt_token(ciphertext: str) -> str:
    """Decrypt a stored GitHub token."""
    return _fernet.decrypt(ciphertext.encode()).decode()
