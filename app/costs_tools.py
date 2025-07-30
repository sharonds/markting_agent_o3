
import os, json

DEFAULTS = {
    "perplexity_per_call_eur": 0.002,   # placeholder; set real values via env
    "dataforseo_per_call_eur": 0.01,
}

def _f(name, default):
    try: return float(os.getenv(name, default))
    except Exception: return default

class ToolCostLedger:
    def __init__(self, artifacts_dir: str):
        self.artifacts_dir = artifacts_dir
        self.by_tool = {}
        self.total_eur = 0.0

    def add(self, tool: str, calls: int = 1, eur: float = None):
        if eur is None:
            if tool == "perplexity":
                eur = calls * _f("COST_PERPLEXITY_PER_CALL_EUR", DEFAULTS["perplexity_per_call_eur"])
            elif tool == "dataforseo":
                eur = calls * _f("COST_DATAFORSEO_PER_CALL_EUR", DEFAULTS["dataforseo_per_call_eur"])
            else:
                eur = 0.0
        self.by_tool[tool] = self.by_tool.get(tool, 0.0) + eur
        self.total_eur += eur
        self._write()

    def _write(self):
        out = {
            "by_tool": self.by_tool,
            "total_eur": round(self.total_eur, 4)
        }
        path = os.path.join(self.artifacts_dir, "tool_usage.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(out, f, indent=2)
