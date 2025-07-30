
import os, json, hashlib, time, random
from typing import Dict, Any

def _env(name: str, default: str = "") -> str:
    v = os.getenv(name)
    return v if v is not None else default

def choose_variant(run_id: str) -> str:
    # If VARIANT explicitly set, use it. Else sample with EXPERIMENT_FRACTION (default 0.0)
    variant = _env("VARIANT", "").strip().lower()
    if variant in ("baseline","treatment"):
        return variant
    exp_fraction = float(_env("EXPERIMENT_FRACTION", "0.0"))
    if exp_fraction <= 0:
        return "baseline"
    # stable hash-based sampling: hash(run_id + experiment_id) -> [0,1)
    exp_id = _env("EXPERIMENT_ID", "")
    h = hashlib.sha1(f"{run_id}|{exp_id}".encode("utf-8")).hexdigest()
    r = (int(h[:8], 16) / 0xFFFFFFFF)
    return "treatment" if r < exp_fraction else "baseline"

def write_experiment_json(artifacts_dir: str, run_id: str):
    exp = {
        "experiment_id": _env("EXPERIMENT_ID", "none"),
        "variant": choose_variant(run_id),
        "scenario": _env("SCENARIO", ""),
        "run_number": int(_env("RUN_NUMBER", "0")),
        "timestamp": int(time.time())
    }
    with open(os.path.join(artifacts_dir, "experiment.json"), "w", encoding="utf-8") as f:
        json.dump(exp, f, indent=2)
    return exp
