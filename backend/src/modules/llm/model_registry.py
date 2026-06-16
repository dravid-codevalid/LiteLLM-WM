# File: model_registry.py. Description: LiteLLM model registry helper. Consists of: utility functions to list and validate supported models against litellm.model_cost.
import litellm


def get_known_models() -> list[str]:
    """Return all model names known to LiteLLM's pricing dictionary."""
    return sorted(litellm.model_cost.keys())


def is_known_model(model_name: str) -> bool:
    return model_name in litellm.model_cost
