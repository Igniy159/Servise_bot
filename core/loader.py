from yaml import safe_load
from pathlib import Path

def load_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return safe_load(f) or {}

def load_config(config_dir: str = "config") -> dict:
    base_path = Path(config_dir)
    raw_date = {}
    for file in base_path.glob("*.yaml"):
        key = file.stem  # rules_alert.yaml -> rules_alert
        raw_date[key] = load_yaml(file)
    return raw_date

raw_config = load_config("C:/Users/User/Desktop/Servise bot/config")
