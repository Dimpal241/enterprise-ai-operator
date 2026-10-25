"""security/secret_manager.py
Enterprise secret helper for environment-based configuration and credentials.
Decouples hardcoded keys and URLs from core agent modules.
"""

from __future__ import annotations
import os
from typing import Optional


def get_redis_url() -> Optional[str]:
    """Retrieve Redis connection URL from environment variable."""
    return os.getenv("REDIS_URL")


def get_secret(key: str, default: Optional[str] = None) -> Optional[str]:
    """Generic helper to fetch sensitive credentials from environment."""
    return os.getenv(key, default)
