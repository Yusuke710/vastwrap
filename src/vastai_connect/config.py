"""Configuration loading for vastai-connect."""

import os
from pathlib import Path

import yaml

_MODULE_DIR = Path(__file__).parent

VALID_CONNECT_MODES = ("ssh", "ide")


def get_startup_script() -> str:
    """Read the startup script from onstart.sh."""
    return (_MODULE_DIR / "onstart.sh").read_text()


def load_config() -> dict:
    """Load default configuration."""
    return yaml.safe_load((_MODULE_DIR / "default_config.yaml").read_text())


def get_connect_mode(config: dict) -> str:
    """Get connection mode: env var > config > default."""
    env_mode = os.environ.get("VAST_MODE", "").lower()
    if env_mode in VALID_CONNECT_MODES:
        return env_mode

    config_mode = config.get("connect_mode", "ssh").lower()
    if config_mode in VALID_CONNECT_MODES:
        return config_mode

    return "ssh"


def get_ide_command(config: dict) -> str:
    """Get IDE command: env var > config > default."""
    return os.environ.get("VAST_IDE") or config.get("ide", "code")
