"""Configuration loading for vastai-connect."""

from pathlib import Path

import yaml

_MODULE_DIR = Path(__file__).parent


def get_startup_script() -> str:
    """Read the startup script from onstart.sh."""
    return (_MODULE_DIR / "onstart.sh").read_text()


def load_config() -> dict:
    """Load default configuration."""
    return yaml.safe_load((_MODULE_DIR / "default_config.yaml").read_text())
