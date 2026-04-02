"""Configuration loader from YAML and environment variables."""

import os
from pathlib import Path
from typing import Optional

import yaml
from dotenv import load_dotenv

from .models import Config, CollectorConfig, ProviderConfig, ModelConfig


def load_config(config_path: Optional[str] = None) -> Config:
    """Load configuration from YAML file and environment variables.

    Args:
        config_path: Path to config.yaml. Defaults to ./config.yaml

    Returns:
        Config object with all settings loaded.
    """
    if config_path is None:
        config_path = "config.yaml"

    # Load .env file
    load_dotenv()

    # Load YAML
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    # Parse collector config
    collector_raw = raw.get("collector", {})
    collector = CollectorConfig(
        interval_minutes=collector_raw.get("interval_minutes", 5),
        timeout_seconds=collector_raw.get("timeout_seconds", 60),
        test_prompt=collector_raw.get("test_prompt", "Hello"),
        max_tokens=collector_raw.get("max_tokens", 100),
    )

    # Parse providers
    providers = []
    for p_raw in raw.get("providers", []):
        provider_name = p_raw["name"]
        api_key = os.getenv(f"{provider_name.upper()}_API_KEY")

        models = [
            ModelConfig(id=m["id"], display_name=m["display_name"])
            for m in p_raw.get("models", [])
        ]

        provider = ProviderConfig(
            name=provider_name,
            display_name=p_raw["display_name"],
            base_url=p_raw["base_url"],
            models=models,
            api_key=api_key,
        )
        providers.append(provider)

    return Config(collector=collector, providers=providers)
