
import os, json, re
from typing import Dict, Any
from collections import Counter
from datetime import datetime

def _read_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

def _read_text(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return ""

def _metrics_core(run_dir: str, db, cost_estimator) -> Dict[str, Any]:
    art = os.path.join(run_dir, "artifacts")
    ev = _read_json(os.path.join(art,"evidence_pack.json")) or {}
    sp = _read_json(os.path.join(art,"strategy_pack.json")) or {}
    cal = _read_json(os.path.join(art,"calendar.json")) or {"items":[]}
    qa = _read_json(os.path.join(art,"qa_report.json")) or {}
    style = _read_json(os.path.join(art,"style_report.json")) or {}
    gateA = _read_json(os.path.join(art,"gateA_report.json")) or {"coverage":[], "missing_total": 0, "low_quality":[]}
    tool_usage = _read_json(os.path.join(art,"tool_usage.json")) or {}

    # Evidence metrics
    facts = ev.get("facts", []) or []
    reachable = [1 for f in facts if f.get("reachable") is True or (f.get("status_code", 0) and int(f.get("status_code",0))<400)]
    provs = [float(f.get("provenance_score", 0.0)) for f in facts if f is not None]
    recency = 0.0
    dated = 0
    for f in facts:
        d = f.get("date")
        if d and re.match(r"^\d{4}-\d{2}-\d{2}$", d):
            dated += 1
    recency = dated/len(facts) if facts else 0.0

    # Gate A
    missing_total = int(gateA.get("missing_total", 0) or 0)
    low_quality = gateA.get("low_quality") or []
    avg_pillar_prov = None
    if gateA.get("coverage"):
        vals = [float(c.get("avg_provenance",0.0)) for c in gateA["coverage"]]
        if vals:
            avg_pillar_prov = round(sum(vals)/len(vals), 3)

    # Calendar / strategy integrity
    pillar_ids = [p.get("id") for p in (sp.get("messaging",{}) or {}).get("pillars",[]) if p.get("id")]
    used_ids = [i.get("pillar_id") for i in (cal.get("items") or []) if i.get("pillar_id")]
    missing_pillars = [pid for pid in pillar_ids if pid not in used_ids]

    # QA/Style
    qa_score = qa.get("score")
    qa_fail = qa.get("failures", [])
    style_flags = (style.get("flags") if isinstance(style, dict) else None) or []

    # Cost (LLM + tools if available)
    total_llm_eur = 0.0
    by_tool = tool_usage.get("by_tool", {})
    total_tool_eur = float(tool_usage.get("total_eur", 0.0) or 0.0)

    if db is not None and cost_estimator is not None:
        try:
            c = db.execute("select coalesce(usage_prompt,0), coalesce(usage_completion,0), model from messages")
            for pin, pout, model in c.fetchall():
                total_llm_eur += cost_estimator(model, {"prompt_tokens": pin, "completion_tokens": pout})
        except Exception:
            pass

    return {
        "evidence": {
            "facts_total": len(facts),
            "reachable_rate": round((sum(reachable)/len(facts)) if facts else 0.0, 3),
            "avg_provenance": round((sum(provs)/len(provs)) if provs else 0.0, 3),
            "dated_ratio": round(recency, 3)
        },
        "gateA": {
            "missing_total": missing_total,
            "avg_pillar_provenance": avg_pillar_prov,
            "low_quality_count": len(low_quality)
        },
        "strategy": {
            "pillar_count": len(pillar_ids),
            "calendar_items": len(cal.get("items") or []),
            "missing_pillars": missing_pillars
        },
        "qa": {
            "score": qa_score,
            "failures": qa_fail
        },
        "style": {
            "flags": style_flags
        },
        "cost": {
            "llm_total_eur": round(total_llm_eur, 4),
            "tool_total_eur": round(total_tool_eur, 4),
            "by_tool": by_tool
        }
    }

def write_metrics(run_dir: str, db=None, cost_estimator=None):
    m = _metrics_core(run_dir, db, cost_estimator)
    out = os.path.join(run_dir, "artifacts", "metrics.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(m, f, indent=2)
    return m
