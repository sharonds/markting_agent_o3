
import os, time, json
from collections import Counter, defaultdict
from app.state import ProjectState, Task, Artifact
from app.logs import EventLogger
from app.agents import researcher, strategist, content_planner, copywriter
from app.db import connect, start_run as db_start_run, end_run as db_end_run, add_task, complete_task, add_artifact, add_gate, resolve_gate
from app.llm_providers import LLMRouter
from app.context_pack import build_context_pack, write_context_pack
from app.costs import estimate
from app.review.qa import generate_qa_report
from app.routing.config import load_routing, apply_env
from app.metrics.collector import write_metrics
from app.experiment.util import write_experiment_json
from app.adapters.context_enrichment import build_external_context

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

def _sum_costs(db):
    try:
        c = db.execute("select model, coalesce(usage_prompt,0), coalesce(usage_completion,0) from messages")
    except Exception:
        return 0.0
    total_eur = 0.0
    for model, pin, pout in c.fetchall():
        total_eur += estimate(model, {"prompt_tokens": pin, "completion_tokens": pout})
    return total_eur

def _costs_by_task(db):
    try:
        c = db.execute("select task_id, model, coalesce(usage_prompt,0), coalesce(usage_completion,0) from messages where task_id is not null")
    except Exception:
        return {}
    by_task = defaultdict(float)
    for task_id, model, pin, pout in c.fetchall():
        by_task[task_id] += estimate(model, {"prompt_tokens": pin, "completion_tokens": pout})
    return dict(by_task)

def _task_roles(db):
    try:
        c = db.execute("select id, role from tasks")
    except Exception:
        return {}
    return {tid: role for (tid, role) in c.fetchall()}

def _read_json(path):
    try:
        return json.load(open(path,"r",encoding="utf-8"))
    except Exception:
        return None

def _quality_summary(artifacts_dir):
    qa = _read_json(os.path.join(artifacts_dir,"qa_report.json")) or {}
    style = _read_json(os.path.join(artifacts_dir,"style_report.json")) or {}
    lines = []
    if qa:
        score = qa.get("score")
        fails = qa.get("failures", [])
        lines.append(f"- qa_score: {score if score is not None else 'n/a'}")
        lines.append(f"- qa_failures: {fails if fails else []}")
    if style:
        lines.append(f"- style_flags: {style.get('flags', [])}")
        lines.append(f"- avg_words_per_sentence: {style.get('avg_words_per_sentence', 'n/a')}")
        lines.append(f"- exclamations: {style.get('exclamations', 'n/a')}")
        lines.append(f"- passive_per_sentence: {style.get('passive_per_sentence', 'n/a')}")
    return "\n".join(lines) if lines else "- (no QA/style artifacts found)"

def run_pipeline(state: ProjectState, run_dir: str, log: EventLogger) -> ProjectState:
    artifacts_dir = os.path.join(run_dir, "artifacts")
    os.makedirs(artifacts_dir, exist_ok=True)

    routing_cfg = load_routing(os.getenv("ROUTING_CONFIG_PATH", "config/routing.yml"))
    resolved = apply_env(routing_cfg)
    with open(os.path.join(artifacts_dir, "routing_resolved.json"), "w", encoding="utf-8") as f:
        json.dump(resolved, f, indent=2)

    db = connect(os.path.join(run_dir, "run.sqlite"))
    temps = {k: v.get("temp", 0.2) for k, v in resolved.items()}
    budget = float(os.getenv("BUDGET_EUR", "0"))
    warn_pct = float(os.getenv("BUDGET_WARN_PCT", "0.8"))
    manifest = {"models": {}, "temps": temps, "budget_eur": budget}
    start_run = os.path.basename(run_dir)
    start_goal = state.intake.get("objective","")
    db_start_run(db, start_run, start_goal, budget, model_info=manifest)

    router = LLMRouter()
    context_pack = build_context_pack(state.compass_meta, state.intake)

    # Experiment metadata and variant
    from app.experiment.util import choose_variant, write_experiment_json
    exp_meta = write_experiment_json(artifacts_dir, start_run)
    variant = (exp_meta.get("variant") or os.getenv("VARIANT","baseline")).lower()

    # Treatment variant: enrich context_pack
    if variant == "treatment":
        ext = build_external_context(start_goal, artifacts_dir)
        if ext.get("sources"):
            context_pack["external_sources"] = ext["sources"]
        if ext.get("keywords"):
            context_pack["keyword_signals"] = ext["keywords"]
        if ext.get("snippet"):
            context_pack["external_context_snippet"] = ext["snippet"]

    from app.context_pack import write_context_pack
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
        "context_pack": context_pack
    }

    warned = False
    aborted = False

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

            spent = _sum_costs(db)
            if budget and not warned and spent >= warn_pct * budget:
                warned = True
                with open(os.path.join(artifacts_dir, "budget_warning.json"), "w", encoding="utf-8") as f:
                    json.dump({"event":"budget_warning", "spent_eur": spent, "budget_eur": budget, "threshold": warn_pct}, f, indent=2)
                log.event("budget_warning", spent_eur=float(spent), budget_eur=float(budget), threshold=warn_pct, role=role)
            if budget and spent > budget:
                log.event("budget_exceeded", spent_eur=float(spent), budget_eur=float(budget), role=role)
                aborted = True
                break

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

                qa = generate_qa_report(artifacts_dir, context_pack)
                qa_path = os.path.join(artifacts_dir, "qa_report.json")
                add_artifact(db, os.path.basename(run_dir), task.id, qa_path, "json", "QA report")

        except Exception as e:
            task.status = "failed"
            complete_task(db, task.id, "failed")
            log.event("task_failed", role=role, task_id=task.id, error=str(e))
            break
        finally:
            ctx["current_task_id"] = None

    by_task_cost = _costs_by_task(db)
    roles = _task_roles(db)
    by_role = defaultdict(float)
    for tid, cost in by_task_cost.items():
        by_role[roles.get(tid, "unknown")] += cost
    spent = _sum_costs(db)

    index_path = os.path.join(run_dir, "SUMMARY.md")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write("# Run Summary\n\n")
        if budget and spent >= warn_pct * budget:
            util = (spent/budget)*100.0
            f.write(f"> ⚠️ **Budget warning**: spent {spent:.2f} / {budget:.2f} EUR ({util:.1f}%) — threshold {int(warn_pct*100)}%\n\n")
        for t in state.tasks:
            f.write(f"- {t.role}: {t.status}\n")
            for a in t.artifacts:
                f.write(f"  - {a.kind}: {a.path} — {a.summary}\n")
        m = _metrics(run_dir)
        f.write("\n---\n## Health metrics\n")
        for k,v in m.items():
            f.write(f"- {k}: {v}\n")
        f.write("\n## Cost\n")
        f.write(f"- total_estimated_eur: {spent:.4f}\n")
        if budget:
            f.write(f"- budget_eur: {budget:.2f}\n")
            f.write(f"- budget_utilization: {((spent/budget)*100.0):.1f}%\n")
        f.write("- by_role:\n")
        for role, cost in by_role.items():
            f.write(f"  - {role}: {cost:.4f}\n")
        f.write("\n## Quality\n")
        # keep simple; QA details already in qa_report.json
        if not os.path.exists(os.path.join(artifacts_dir,"qa_report.json")):
            f.write("- (no QA/style artifacts found)\n")

    write_metrics(run_dir, db=db, cost_estimator=estimate)
    status = "aborted" if (budget and spent > budget) else "completed"
    db_end_run(db, os.path.basename(run_dir), status)
    log.event("run_completed", spent_eur=float(spent), status=status)
    return state
