"""Environment helpers for Django settings.

`.env` loading is a dev convenience: python-dotenv is a dev-only dependency,
so the load is skipped when it isn't installed. Production exports real
environment variables instead; those always take precedence over `.env`.
"""

import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

try:
    from dotenv import load_dotenv as _load_dotenv
except ImportError:  # python-dotenv not installed (non-dev install)
    _load_dotenv = None


def load_env_file(path: Path) -> None:
    """Load a .env file into os.environ when python-dotenv is available."""
    if _load_dotenv is not None:
        _load_dotenv(path)


def env(name: str) -> str:
    """A required environment variable — no silent defaults."""
    try:
        return os.environ[name]
    except KeyError:
        raise ImproperlyConfigured(
            f"Missing required environment variable {name!r}; "
            "copy .env.example to .env (or export it)"
        ) from None
