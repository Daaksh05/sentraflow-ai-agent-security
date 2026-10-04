"""AI Model Provider module exports and factory."""

from app.ai.base import ModelProvider
from app.ai.nemotron import MockModelProvider, NemotronProvider
from app.core.config import settings


def get_model_provider(provider_type: str = settings.AI_MODEL_PROVIDER) -> ModelProvider:
    """Factory function returning the configured ModelProvider instance."""
    normalized = provider_type.lower()
    if normalized in ("nemotron", "nemotron_api", "nemotron_nim"):
        return NemotronProvider()
    return MockModelProvider()


__all__ = ["ModelProvider", "MockModelProvider", "NemotronProvider", "get_model_provider"]
