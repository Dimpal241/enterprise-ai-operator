"""secrets.py
Utility module for fetching secrets from environment variables.
Provides a simple wrapper that can be extended for secret managers.
"""

import os
from typing import Optional


def get_redis_url() -> Optional[str]:
    """Return the Redis connection URL from the environment.

    The function looks for a ``REDIS_URL`` variable; if not set, returns ``None``.
    This allows callers to provide a fallback.
    """
    return os.getenv("REDIS_URL")

# Additional secret getters can be added here in the future.
