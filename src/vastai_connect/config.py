"""Configuration loading for vastai-connect."""

import os
from pathlib import Path

import yaml

_MODULE_DIR = Path(__file__).parent

VALID_CONNECT_MODES = ("cli", "vscode", "cursor")


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

    config_mode = config.get("connect_mode", "cli").lower()
    if config_mode in VALID_CONNECT_MODES:
        return config_mode

    return "cli"


def get_disk_size(config: dict) -> int:
    """Get disk size in GB: env var > config > default (10GB)."""
    env_disk = os.environ.get("VAST_DISK", "")
    if env_disk.isdigit() and int(env_disk) > 0:
        return int(env_disk)

    config_disk = config.get("disk", 10)
    if isinstance(config_disk, int) and config_disk > 0:
        return config_disk

    return 10
