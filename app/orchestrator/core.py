
import os, time, json
from collections import Counter
from app.state import ProjectState, Task, Artifact
from app.logs import EventLogger
from app.agents import researcher, strategist, content_planner, copywriter
from app.db import connect, start_run as db_start_run, end_run as db_end_run, add_task, complete_task, add_artifact, add_gate, resolve_gate
from app.llm_providers import LLMRouter
from app.context_pack import build_context_pack, write_context_pack
from app.costs import estimate
from app.memory.store import open_db as mem_open, load_snapshot as mem_load, persist_from_artifacts as mem_persist

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

def run_pipeline(state: ProjectState, run_dir: str, log: EventLogger) -> ProjectState:
    artifacts_dir = os.path.join(run_dir, "artifacts")
    os.makedirs(artifacts_dir, exist_ok=True)

    db = connect(os.path.join(run_dir, "run.sqlite"))
    manifest = {
        "models": {},
        "temps": {"researcher":0.2,"strategist":0.3,"content_planner":0.2,"copywriter":0.7},
        "budget_eur": float(os.getenv("BUDGET_EUR", "0"))
    }
    db_start_run(db, os.path.basename(run_dir), state.intake.get("objective",""), manifest.get("budget_eur", 0), model_info=manifest)

    router = LLMRouter()

    # Cross-run memory
    mem_read = os.getenv("MEMORY_READ", "1") == "1"
    mem_write = os.getenv("MEMORY_WRITE", "1") == "1"
    memory_snapshot = {"facts": [], "segments": [], "pillars": [], "stats": {"facts_total":0,"segments_total":0,"pillars_total":0}}
    if mem_read:
        mdb = mem_open(os.getenv("MEMORY_DB_PATH"))
        memory_snapshot = mem_load(mdb)
        with open(os.path.join(artifacts_dir, "memory_snapshot.json"), "w", encoding="utf-8") as f:
            json.dump(memory_snapshot, f, indent=2, ensure_ascii=False)

    context_pack = build_context_pack(state.compass_meta, state.intake)
    context_pack["memory_stats"] = memory_snapshot.get("stats", {})
    write_context_pack(os.path.join(artifacts_dir,"context_pack.json"), context_pack)

    ctx = {
        "compass_meta": state.compass_meta,
        "compass_body": state.compass_body,
        "intake": state.intake,
        "paths": {"run": run_dir, "artifacts": artifacts_dir, "prompts": os.path.join(run_dir,"prompts"), "responses": os.path.join(run_dir,"responses")},
        "llm_router": router,
        "db": db,
        "run_id": os.path.basename(run_dir),
        "current_task_id": None,
        "context_pack": context_pack,
        "memory": memory_snapshot
    }

    for role, goal in PIPELINE:
        task = Task(id=f"{int(time.time())}-{role}", role=role, goal=goal)
        state.tasks.append(task)
        log.event("task_started", role=role, goal=goal, task_id=task.id)
        add_task(db, os.path.basename(run_dir), task.id, role, goal)
        ctx["current_task_id"] = task.id
        try:
            arts = AGENTS[role]({}, ctx)
            for a in arts:
                state.artifacts.append(a)
                task.artifacts.append(a)
                add_artifact(db, os.path.basename(run_dir), task.id, a.path, a.kind, a.summary)
            task.status = "done"
            complete_task(db, task.id, "done")
            log.event("task_completed", role=role, task_id=task.id, artifacts=[a.path for a in arts])

            if role == "strategist":
                gate_summary = "Review ICP + Positioning + Messaging (Gate A)"
                add_gate(db, os.path.basename(run_dir), task.id, "GATE_A_POSITIONING", gate_summary)
                with open(os.path.join(run_dir, "pending_gate.json"), "w", encoding="utf-8") as f:
                    json.dump({"gate":"GATE_A_POSITIONING","summary":gate_summary,"task_id":task.id}, f, indent=2)
                log.event("gate_waiting", gate="GATE_A_POSITIONING")
                if os.getenv("AUTO_APPROVE","0") != "1":
                    input(">> Gate A waiting. Press Enter to approve...")
                resolve_gate(db, os.path.basename(run_dir), task.id, "GATE_A_POSITIONING", "approved")
                log.event("gate_resumed", gate="GATE_A_POSITIONING")

            if role == "copywriter":
                gate_summary = "Review First Asset (Gate B)"
                add_gate(db, os.path.basename(run_dir), task.id, "GATE_B_FIRST_ASSET", gate_summary)
                with open(os.path.join(run_dir, "pending_gate.json"), "w", encoding="utf-8") as f:
                    json.dump({"gate":"GATE_B_FIRST_ASSET","summary":gate_summary,"task_id":task.id}, f, indent=2)
                log.event("gate_waiting", gate="GATE_B_FIRST_ASSET")
                if os.getenv("AUTO_APPROVE","0") != "1":
                    input(">> Gate B waiting. Press Enter to approve...")
                resolve_gate(db, os.path.basename(run_dir), task.id, "GATE_B_FIRST_ASSET", "approved")
                log.event("gate_resumed", gate="GATE_B_FIRST_ASSET")

        except Exception as e:
            task.status = "failed"
            complete_task(db, task.id, "failed")
            log.event("task_failed", role=role, task_id=task.id, error=str(e))
            break
        finally:
            ctx["current_task_id"] = None

    if mem_write:
        try:
            ev = json.load(open(os.path.join(artifacts_dir,"evidence_pack.json"),"r",encoding="utf-8"))
            sp = json.load(open(os.path.join(artifacts_dir,"strategy_pack.json"),"r",encoding="utf-8"))
            mdb = mem_open(os.getenv("MEMORY_DB_PATH"))
            counts = mem_persist(mdb, ev, sp)
            with open(os.path.join(artifacts_dir, "memory_persist_report.json"), "w", encoding="utf-8") as f:
                json.dump({"upserted": counts}, f, indent=2)
        except Exception as e:
            with open(os.path.join(artifacts_dir, "memory_persist_report.json"), "w", encoding="utf-8") as f:
                json.dump({"error": str(e)}, f, indent=2)

    index_path = os.path.join(run_dir, "SUMMARY.md")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write("# Run Summary\n\n")
        for t in state.tasks:
            f.write(f"- {t.role}: {t.status}\n")
            for a in t.artifacts:
                f.write(f"  - {a.kind}: {a.path} — {a.summary}\n")
        m = _metrics(run_dir)
        f.write("\n---\n")
        f.write("## Health metrics\n")
        for k,v in m.items():
            f.write(f"- {k}: {v}\n")

    db_end_run(db, os.path.basename(run_dir), "completed")
    log.event("run_completed")
    return state
