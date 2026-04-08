"""Data models for configuration and metrics."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ModelConfig:
    """Model configuration."""
    id: str
    display_name: str


@dataclass
class ProviderConfig:
    """Provider configuration."""
    name: str
    display_name: str
    base_url: str
    models: list[ModelConfig] = field(default_factory=list)
    api_key: Optional[str] = None  # Loaded from .env


@dataclass
class CollectorConfig:
    """Collector settings."""
    interval_minutes: int = 5
    timeout_seconds: int = 60
    test_prompt: str = "Hello"
    max_tokens: int = 100


@dataclass
class Config:
    """Root configuration."""
    collector: CollectorConfig = field(default_factory=CollectorConfig)
    providers: list[ProviderConfig] = field(default_factory=list)


@dataclass
class MetricResult:
    """Result of a single model test."""
    provider_name: str
    model_id: str
    ttft_ms: Optional[float] = None
    total_time_ms: Optional[float] = None
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    tokens_per_second: Optional[float] = None
    success: bool = False
    error_message: Optional[str] = None
