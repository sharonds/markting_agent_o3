
import os, time, json
from collections import Counter
from app.state import ProjectState, Task, Artifact
from app.logs import EventLogger
from app.agents import researcher, strategist, content_planner, copywriter
from app.db import connect, start_run as db_start_run, end_run as db_end_run, add_task, complete_task, add_artifact, add_gate, resolve_gate
from app.llm_providers import LLMRouter
from app.context_pack import build_context_pack, write_context_pack
from app.costs import estimate

AGENTS = {
    "researcher": researcher.run,
    "strategist": strategist.run,
    "content_planner": content_planner.run,
    "copywriter": copywriter.run
}

PIPELINE = [
    ("researcher", "Compile research/evidence pack"),
    ("strategist", "Draft ICP + positioning + messaging"),
    ("content_planner", "Build content calendar from timeline/channels"),
    ("copywriter", "Draft first LinkedIn post"),
]

def _metrics(run_dir):
    base = os.path.join(run_dir, "artifacts")
    def _load(fn):
        p=os.path.join(base, fn)
        return json.load(open(p,"r",encoding="utf-8")) if os.path.exists(p) else None
    ev=_load("evidence_pack.json") or {}
    sp=_load("strategy_pack.json") or {}
    cal=_load("calendar.json") or {}
    facts=len(ev.get("facts",[]))
    comps=len(ev.get("competitors",[]))
    kws=len(ev.get("keywords",[]))
    segs=len((sp.get("icp") or {}).get("segments",[]))
    pillars=(sp.get("messaging") or {}).get("pillars",[])
    pcount=len(pillars)
    intents=Counter(i.get("intent","") for i in cal.get("items",[]))
    pid_set={p.get("id") for p in pillars}
    bad_calendar=[i for i in cal.get("items",[]) if i.get("pillar_id") not in pid_set]
    return {
        "facts":facts,"competitors":comps,"keyword_clusters":kws,
        "icp_segments":segs,"pillars":pcount,
        "calendar_items":len(cal.get("items",[])),"intent_counts":dict(intents),
        "calendar_pillar_mismatches":len(bad_calendar)
    }

def _gateA_report(run_dir):
    base = os.path.join(run_dir, "artifacts")
    ev = json.load(open(os.path.join(base,"evidence_pack.json"),"r",encoding="utf-8"))
    sp = json.load(open(os.path.join(base,"strategy_pack.json"),"r",encoding="utf-8"))
    fact_by_id = {f["id"]: f for f in ev.get("facts",[]) if "id" in f}
    pillars = (sp.get("messaging") or {}).get("pillars",[])
    coverage = []
    low_quality = []
    for p in pillars:
        eids = p.get("evidence_ids", [])
        resolved = [eid for eid in eids if eid in fact_by_id]
        missing = [eid for eid in eids if eid not in fact_by_id]
        prov_scores = [float(fact_by_id[eid].get("provenance_score", 0.0)) for eid in resolved] or [0.0]
        avg_prov = round(sum(prov_scores)/len(prov_scores), 3)
        row = {
            "pillar_id": p.get("id"),
            "name": p.get("name"),
            "evidence_ids": eids,
            "resolved": resolved,
            "missing": missing,
            "avg_provenance": avg_prov
        }
        coverage.append(row)
        if avg_prov < float(os.getenv("PROVENANCE_MIN_AVG", "0.5")):
            low_quality.append({"pillar_id": p.get("id"), "avg_provenance": avg_prov})
    out = {"coverage": coverage, "missing_total": sum(len(r["missing"]) for r in coverage), "low_quality": low_quality}
    json.dump(out, open(os.path.join(base,"gateA_report.json"),"w",encoding="utf-8"), indent=2)
    return out
