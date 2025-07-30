
import os, json
from typing import Dict, Any
try:
    import yaml
except Exception:
    yaml = None

DEFAULT = {
    "researcher": {"provider": "openai", "temp": 0.2},
    "strategist": {"provider": "anthropic", "temp": 0.3},
    "content_planner": {"provider": "openai", "temp": 0.2},
    "copywriter": {"provider": "openai", "temp": 0.7},
}

def load_routing(path: str = "config/routing.yml") -> Dict[str, Any]:
    cfg = {}
    if yaml and os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                cfg = yaml.safe_load(f) or {}
        except Exception:
            cfg = {}
    # merge with defaults
    out = DEFAULT.copy()
    out.update({k: v for k, v in (cfg or {}).items() if isinstance(v, dict)})
    return out

def apply_env(routing: Dict[str, Any]) -> Dict[str, Any]:
    resolved = {}
    for role, spec in routing.items():
        prov = (spec.get("provider") or "").lower().strip() or "openai"
        temp = float(spec.get("temp") or 0.2)
        env_key = f"LLM_{role.upper()}"
        os.environ[env_key] = prov
        # keep temps in environment so orchestrator/agents can read
        os.environ[f"TEMP_{role.upper()}"] = str(temp)
        resolved[role] = {"provider": prov, "temp": temp}
    return resolved
