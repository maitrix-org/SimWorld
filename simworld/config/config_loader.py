import yaml
from pathlib import Path
import os

class Config:
    def __init__(self, path: str = None):
        default_path = Path(__file__).parent / "default.yaml"
        config_path = Path(path) if path else default_path

        with open(default_path, "r") as f:
            self.default_config = yaml.safe_load(f) or {}

        if config_path != default_path and config_path.exists():
            with open(config_path, "r") as f:
                user_config = yaml.safe_load(f) or {}
                self._merge_dicts(self.default_config, user_config)

        self.config = self.default_config

    def get(self, key_path: str, default=None):
        keys = key_path.split(".")
        value = self.config
        for key in keys:
            if not isinstance(value, dict) or key not in value:
                if not default is None:
                    return default
                raise ValueError(f"Key {key_path} not found in config")
            value = value[key]
        return value

    def __getitem__(self, key_path: str):
        return self.get(key_path)

    def _merge_dicts(self, base, updates):
        """Recursively merge updates into base config."""
        for k, v in updates.items():
            if isinstance(v, dict) and isinstance(base.get(k), dict):
                self._merge_dicts(base[k], v)
            else:
                base[k] = v


