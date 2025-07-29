
import os

def _get_float(name, default):
    try:
        return float(os.getenv(name, default))
    except Exception:
        return default

OPENAI_IN_PERK = _get_float("COST_OPENAI_INPUT_PER1K", 0.0)
OPENAI_OUT_PERK = _get_float("COST_OPENAI_OUTPUT_PER1K", 0.0)
ANTHROPIC_IN_PERK = _get_float("COST_ANTHROPIC_INPUT_PER1K", 0.0)
ANTHROPIC_OUT_PERK = _get_float("COST_ANTHROPIC_OUTPUT_PER1K", 0.0)

def estimate(provider_name: str, usage: dict) -> float:
    if not usage:
        return 0.0
    pin = usage.get("prompt_tokens") or 0
    pout = usage.get("completion_tokens") or 0
    if provider_name == "openai":
        return (pin/1000.0)*OPENAI_IN_PERK + (pout/1000.0)*OPENAI_OUT_PERK
    if provider_name == "anthropic":
        return (pin/1000.0)*ANTHROPIC_IN_PERK + (pout/1000.0)*ANTHROPIC_OUT_PERK
    return 0.0
