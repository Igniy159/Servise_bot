import yaml
from pathlib import Path


def load_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}

def load_config(config_dir: str = "config") -> dict:
    base_path = Path(config_dir)
    config = {}
    for file in base_path.glob("*.yaml"):
        key = file.stem  # rules_alert.yaml -> rules_alert
        config[key] = load_yaml(file)
    return config

config = load_config("C:/Users/User/Desktop/Servise bot/config")
