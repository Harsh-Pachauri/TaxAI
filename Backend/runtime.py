from __future__ import annotations

from typing import Any

from config import Config


_runtime_config: Any = Config


def set_runtime_config(config: Any) -> None:
    global _runtime_config
    _runtime_config = config


def get_runtime_config() -> Any:
    return _runtime_config
