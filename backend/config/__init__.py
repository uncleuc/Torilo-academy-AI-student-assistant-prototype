"""Central application settings and logging configuration."""

from backend.config.logging_config import configure_logging
from backend.config.settings import Settings, get_settings

__all__ = ["Settings", "configure_logging", "get_settings"]