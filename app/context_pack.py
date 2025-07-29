
import os, json
from datetime import datetime

def infer_locale(geos):
    geos = [g.upper() for g in (geos or [])]
    if "UK" in geos or "EU" in geos:
        return "en-GB"
    return "en-US"

def build_context_pack(compass_meta: dict, intake: dict) -> dict:
    brand = compass_meta.get("brand") or intake.get("brand") or "Brand"
    voice = compass_meta.get("voice") or []
    guardrails = compass_meta.get("guardrails") or {}
    channels = intake.get("channels") or []
    geos = intake.get("geos") or []
    locale = infer_locale(geos)
    timeline = intake.get("timeline") or {}
    audience = intake.get("audience") or ""
    ctas = compass_meta.get("ctas") or []
    return {
        "brand": brand,
        "voice": voice,
        "guardrails": guardrails,
        "audience": audience,
        "geos": geos,
        "locale": locale,
        "channels": channels,
        "timeline": timeline,
        "ctas": ctas
    }

def write_context_pack(path: str, pack: dict):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(pack, f, indent=2, ensure_ascii=False)
